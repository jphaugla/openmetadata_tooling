#!/usr/bin/env python3
import sys
import time
import os
import json
import urllib.parse
from om_client import OpenMetadataClient

def measure_individual_tables(client, fqn, table_query_param):
    print(f"\n⏱️  [Method 1] Starting Individual Table Loop Export/Import...")
    
    # Fetch tables belonging to this asset scope
    encoded_fqn = urllib.parse.quote(fqn)
    url = f"/tables?{table_query_param}={encoded_fqn}&limit=1000"
    resp = client._make_request("GET", url)
    
    if not resp or resp.status_code != 200:
        print(f"❌ Failed to fetch tables for: {fqn}")
        return None, None
        
    tables_data = resp.json().get("data", [])
    if not tables_data:
        print(f"⚠️  No tables found for {fqn} to benchmark.")
        return 0, 0
        
    print(f"  Found {len(tables_data)} tables to benchmark.")
    
    # 1. Export Phase
    export_start = time.time()
    table_csvs = {}
    for table in tables_data:
        t_fqn = table.get("fullyQualifiedName")
        encoded_t_fqn = urllib.parse.quote(t_fqn)
        print(f"    ➡️ Exporting table: {t_fqn}")
        t_resp = client._make_request("GET", f"/tables/name/{encoded_t_fqn}/export")
        if t_resp and t_resp.status_code == 200:
            table_csvs[t_fqn] = t_resp.text
        else:
            print(f"    ❌ Export failed for {t_fqn}")
    export_duration = time.time() - export_start
    
    # 2. Import Phase
    import_start = time.time()
    client.headers["Content-Type"] = "text/plain"
    
    for t_fqn, csv_text in table_csvs.items():
        encoded_t_fqn = urllib.parse.quote(t_fqn)
        print(f"    ⬅️ Importing table: {t_fqn}")
        t_resp = client._make_request("PUT", f"/tables/name/{encoded_t_fqn}/import", data=csv_text)
        if t_resp is None or t_resp.status_code != 200:
            print(f"    ❌ Import failed for {t_fqn}")
            
    client.headers["Content-Type"] = "application/json"
    import_duration = time.time() - import_start
    
    return export_duration, import_duration

def measure_bulk_csv_file(client, fqn, endpoint_prefix, csv_file_path, fqn_type):
    print(f"\n⏱️  [Method 2] Starting Bulk File-Based Export/Import ({fqn_type})...")
    encoded_fqn = urllib.parse.quote(fqn)
    
    # 1. Export Phase (Save to CSV File)
    export_start = time.time()
    resp = client._make_request("GET", f"/{endpoint_prefix}/name/{encoded_fqn}/export")
    
    if not resp or resp.status_code != 200:
        print(f"❌ Bulk Export failed for: {fqn}")
        return None, None
        
    with open(csv_file_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    export_duration = time.time() - export_start
    print(f"  ✅ Export complete. Written to {csv_file_path}")
    
    # 2. Import Phase (Read from CSV File)
    import_start = time.time()
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found for import phase: {csv_file_path}")
        return export_duration, None
        
    with open(csv_file_path, "r", encoding="utf-8") as f:
        csv_data = f.read()
        
    client.headers["Content-Type"] = "text/plain"
    resp_imp = client._make_request("PUT", f"/{endpoint_prefix}/name/{encoded_fqn}/import", data=csv_data)
    client.headers["Content-Type"] = "application/json"
    import_duration = time.time() - import_start
    
    if not resp_imp or resp_imp.status_code != 200:
        print(f"❌ Bulk Import failed for: {fqn}")
        return export_duration, None
        
    print(f"  ✅ Import complete using CSV file asset transfer.")
    return export_duration, import_duration

def measure_pure_bulk_dump_load(client, fqn, endpoint_prefix, fqn_type):
    print(f"\n⏱️  [Method 3] Starting Pure In-Memory {fqn_type} Dump/Load Test...")
    encoded_fqn = urllib.parse.quote(fqn)
    
    # 1. Export Phase (In-Memory String)
    export_start = time.time()
    resp = client._make_request("GET", f"/{endpoint_prefix}/name/{encoded_fqn}/export")
    export_duration = time.time() - export_start
    
    if not resp or resp.status_code != 200:
        print(f"❌ Pure Bulk Export failed for: {fqn}")
        return None, None
        
    csv_data = resp.text
    
    # 2. Import Phase (Direct Payload Stream)
    import_start = time.time()
    client.headers["Content-Type"] = "text/plain"
    resp_imp = client._make_request("PUT", f"/{endpoint_prefix}/name/{encoded_fqn}/import", data=csv_data)
    client.headers["Content-Type"] = "application/json"
    import_duration = time.time() - import_start
    
    if not resp_imp or resp_imp.status_code != 200:
        print(f"❌ Pure Bulk Import failed for: {fqn}")
        return export_duration, None
        
    print(f"  ✅ Pure In-Memory bulk transfer complete.")
    return export_duration, import_duration

def measure_tables_bulk_endpoint(client, fqn, table_query_param, json_file_path, fqn_type):
    print(f"\n⏱️  [Method 4] Starting Tables Bulk Endpoint Export/Import (/tables/bulk)...")
    
    # 1. Export Phase (Fetch array via standard API & translate into CreateTableRequest payloads)
    export_start = time.time()
    encoded_fqn = urllib.parse.quote(fqn)
    url = f"/tables?{table_query_param}={encoded_fqn}&limit=1000"
    resp = client._make_request("GET", url)
    
    if not resp or resp.status_code != 200:
        print(f"❌ Bulk Tables Export preparation failed for: {fqn}")
        return None, None
        
    raw_tables = resp.json().get("data", [])
    sanitized_requests = []
    
    for table in raw_tables:
        # Resolve parent schema reference string cleanly
        schema_fqn = fqn if fqn_type == "Database Schema" else table.get("databaseSchema", {}).get("fullyQualifiedName")
        if not schema_fqn:
            continue
            
        create_req = {
            "name": table.get("name"),
            "displayName": table.get("displayName"),
            "description": table.get("description"),
            "tableType": table.get("tableType", "Regular"),
            "databaseSchema": schema_fqn,
            "columns": []
        }
        
        # Transform column schemas to match validation constraints
        for col in table.get("columns", []):
            col_req = {
                "name": col.get("name"),
                "dataType": col.get("dataType"),
                "description": col.get("description"),
                "dataLength": col.get("dataLength"),
                "precision": col.get("precision"),
                "scale": col.get("scale"),
                "constraint": col.get("constraint")
            }
            # Clean up empty optional nodes to reduce footprint noise
            col_req = {k: v for k, v in col_req.items() if v is not None}
            create_req["columns"].append(col_req)
            
        if table.get("owners"):
            create_req["owners"] = table.get("owners")
        if table.get("tags"):
            create_req["tags"] = table.get("tags")
            
        sanitized_requests.append(create_req)
        
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(sanitized_requests, f, indent=2)
        
    export_duration = time.time() - export_start
    print(f"  ✅ Export complete (sanitized {len(sanitized_requests)} tables into CreateTableRequest format). Written to {json_file_path}")
    
    # 2. Import Phase (Push sanitized JSON schema array payload back to bulk endpoint)
    import_start = time.time()
    if not os.path.exists(json_file_path):
        print(f"❌ File not found for bulk import phase: {json_file_path}")
        return export_duration, None
        
    with open(json_file_path, "r", encoding="utf-8") as f:
        payload_data = json.load(f)
        
    resp_imp = client._make_request("PUT", "/tables/bulk", json=payload_data)
        
    import_duration = time.time() - import_start
    
    if not resp_imp or resp_imp.status_code not in [200, 201]:
        status_code = resp_imp.status_code if resp_imp else "Unknown"
        if resp_imp:
            print(f"    ❌ Server Response Error Text: {resp_imp.text}")
        print(f"❌ Tables Bulk Import failed at /tables/bulk (Status Code: {status_code})")
        return export_duration, None
        
    print(f"  ✅ Import complete using /tables/bulk endpoint.")
    return export_duration, import_duration

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python table_load_comparison.py <database_or_schema_fqn>")
        print("Examples:")
        print("  Schema: python table_load_comparison.py Enterprise_SE.CUSTOMERS.COLLATE_SE")
        print("  Database: python table_load_comparison.py Enterprise_SE.CUSTOMERS")
        sys.exit(1)

    fqn = sys.argv[1]
    parts = fqn.split('.')
    
    if len(parts) >= 3:
        fqn_type = "Database Schema"
        table_query_param = "databaseSchema"
        endpoint_prefix = "databaseSchemas"
    else:
        fqn_type = "Database"
        table_query_param = "database"
        endpoint_prefix = "databases"

    json_dir = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    os.makedirs(json_dir, exist_ok=True)
    
    method2_csv_path = os.path.join(json_dir, f"{fqn}.csv")
    method4_json_path = os.path.join(json_dir, f"{fqn}_tables_bulk.json")

    client = OpenMetadataClient()
    
    print(f"🚀 Starting Benchmarks for {fqn_type}: {fqn}")
    
    m1_exp, m1_imp = measure_individual_tables(client, fqn, table_query_param)
    m2_exp, m2_imp = measure_bulk_csv_file(client, fqn, endpoint_prefix, method2_csv_path, fqn_type)
    m3_exp, m3_imp = measure_pure_bulk_dump_load(client, fqn, endpoint_prefix, fqn_type)
    m4_exp, m4_imp = measure_tables_bulk_endpoint(client, fqn, table_query_param, method4_json_path, fqn_type)
    
    print("\n" + "="*75)
    print(f"{'METRIC COMPARISON':<42} | {'EXPORT TIME':<13} | {'IMPORT TIME':<13}")
    print("="*75)
    
    def format_time(t):
        return f"{t:.4f}s" if t is not None else "FAILED"
        
    print(f"{'1. Individual Table Loop':<42} | {format_time(m1_exp):<13} | {format_time(m1_imp):<13}")
    print(f"{f'2. Bulk CSV File ({fqn_type})':<42} | {format_time(m2_exp):<13} | {format_time(m2_imp):<13}")
    print(f"{f'3. Pure Bulk Dump/Load ({fqn_type})':<42} | {format_time(m3_exp):<13} | {format_time(m3_imp):<13}")
    print(f"{'4. Bulk Tables Endpoint (/tables/bulk)':<42} | {format_time(m4_exp):<13} | {format_time(m4_imp):<13}")
    print("-"*75)
    
    if m1_exp and m4_exp and m4_exp > 0:
        print(f"💡 /tables/bulk Export is {m1_exp / m4_exp:.2f}x faster than Table Looping.")
    if m1_imp and m4_imp and m4_imp > 0:
        print(f"💡 /tables/bulk Import is {m1_imp / m4_imp:.2f}x faster than Table Looping.")
    print("="*75)

if __name__ == "__main__":
    main()

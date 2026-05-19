#!/usr/bin/env python3
import sys
import time
import os
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

def measure_bulk_csv_file(client, fqn, endpoint_prefix, csv_file_path):
    print(f"\n⏱️  [Method 2] Starting Bulk File-Based Export/Import ({csv_file_path})...")
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

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python table_load_comparison.py <database_or_schema_fqn>")
        print("Examples:")
        print("  Schema: python table_load_comparison.py Enterprise_SE.CUSTOMERS.COLLATE_SE")
        print("  Database: python table_load_comparison.py Enterprise_SE.CUSTOMERS")
        sys.exit(1)

    fqn = sys.argv[1]
    parts = fqn.split('.')
    
    # Dynamically pivot parameters depending on context depth
    if len(parts) >= 3:
        fqn_type = "Database Schema"
        table_query_param = "databaseSchema"
        endpoint_prefix = "databaseSchemas"
    else:
        fqn_type = "Database"
        table_query_param = "database"
        endpoint_prefix = "databases"

    # Set up JSON_DIR pathing matching your other tools
    json_dir = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    os.makedirs(json_dir, exist_ok=True)
    csv_file_path = os.path.join(json_dir, f"{fqn}.csv")

    client = OpenMetadataClient()
    
    print(f"🚀 Starting Benchmarks for {fqn_type}: {fqn}")
    print(f"📂 Output File Destination: {csv_file_path}")
    
    # Execute the two narrowed down target methods
    m1_exp, m1_imp = measure_individual_tables(client, fqn, table_query_param)
    m2_exp, m2_imp = measure_bulk_csv_file(client, fqn, endpoint_prefix, csv_file_path)
    
    # Output Comparative Performance Summary
    print("\n" + "="*70)
    print(f"{'METRIC COMPARISON':<38} | {'EXPORT TIME':<13} | {'IMPORT TIME':<13}")
    print("="*70)
    
    def format_time(t):
        return f"{t:.4f}s" if t is not None else "FAILED"
        
    print(f"{'1. Individual Table Loop':<38} | {format_time(m1_exp):<13} | {format_time(m1_imp):<13}")
    print(f"{f'2. Bulk CSV File ({fqn_type})':<38} | {format_time(m2_exp):<13} | {format_time(m2_imp):<13}")
    print("-"*70)
    
    if m1_exp and m2_exp and m2_exp > 0:
        print(f"💡 Bulk CSV Export is {m1_exp / m2_exp:.2f}x faster than Table Looping.")
    if m1_imp and m2_imp and m2_imp > 0:
        print(f"💡 Bulk CSV Import is {m1_imp / m2_imp:.2f}x faster than Table Looping.")
    print("="*70)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys
import time
import urllib.parse
from om_client import OpenMetadataClient

def measure_individual_tables(client, schema_fqn):
    print("\n⏱️  [Method 1] Starting Individual Table Loop Export/Import...")
    
    # Fetch tables belonging to this schema
    encoded_schema = urllib.parse.quote(schema_fqn)
    url = f"/tables?databaseSchema={encoded_schema}&limit=1000"
    resp = client._make_request("GET", url)
    
    if not resp or resp.status_code != 200:
        print(f"❌ Failed to fetch tables for schema: {schema_fqn}")
        return None, None
        
    tables_data = resp.json().get("data", [])
    if not tables_data:
        print(f"⚠️  No tables found in schema {schema_fqn} to benchmark.")
        return 0, 0
        
    print(f"  Found {len(tables_data)} tables to benchmark.")
    
    # 1. Export Phase
    export_start = time.time()
    table_csvs = {}
    for table in tables_data:
        fqn = table.get("fullyQualifiedName")
        encoded_fqn = urllib.parse.quote(fqn)
        print(f"    ➡️ Exporting table: {fqn}")
        t_resp = client._make_request("GET", f"/tables/name/{encoded_fqn}/export")
        if t_resp and t_resp.status_code == 200:
            table_csvs[fqn] = t_resp.text
        else:
            print(f"    ❌ Export failed for {fqn}")
    export_duration = time.time() - export_start
    
    # 2. Import Phase
    import_start = time.time()
    client.headers["Content-Type"] = "text/plain"
    
    for fqn, csv_text in table_csvs.items():
        encoded_fqn = urllib.parse.quote(fqn)
        print(f"    ⬅️ Importing table: {fqn}")
        t_resp = client._make_request("PUT", f"/tables/name/{encoded_fqn}/import", data=csv_text)
        if t_resp is None or t_resp.status_code != 200:
            print(f"    ❌ Import failed for {fqn}")
            
    client.headers["Content-Type"] = "application/json"
    import_duration = time.time() - import_start
    
    return export_duration, import_duration

def measure_schema_bulk(client, schema_fqn):
    print("\n⏱️  [Method 2] Starting Bulk Database Schema Export/Import...")
    encoded_schema = urllib.parse.quote(schema_fqn)
    
    # 1. Export Phase
    export_start = time.time()
    resp = client._make_request("GET", f"/databaseSchemas/name/{encoded_schema}/export")
    export_duration = time.time() - export_start
    
    if not resp or resp.status_code != 200:
        print(f"❌ Bulk Schema Export failed for: {schema_fqn}")
        return None, None
        
    csv_text = resp.text
    
    # 2. Import Phase
    import_start = time.time()
    client.headers["Content-Type"] = "text/plain"
    resp_imp = client._make_request("PUT", f"/databaseSchemas/name/{encoded_schema}/import", data=csv_text)
    client.headers["Content-Type"] = "application/json"
    import_duration = time.time() - import_start
    
    if not resp_imp or resp_imp.status_code != 200:
        print(f"❌ Bulk Schema Import failed for: {schema_fqn}")
        return export_duration, None
        
    return export_duration, import_duration

def measure_database_bulk(client, database_fqn):
    print("\n⏱️  [Method 3] Starting Full Database Dump (Database Bulk Export/Import)...")
    encoded_db = urllib.parse.quote(database_fqn)
    
    # 1. Export Phase
    export_start = time.time()
    resp = client._make_request("GET", f"/databases/name/{encoded_db}/export")
    export_duration = time.time() - export_start
    
    if not resp or resp.status_code != 200:
        print(f"❌ Database Dump Export failed for: {database_fqn}")
        return None, None
        
    csv_text = resp.text
    
    # 2. Import Phase
    import_start = time.time()
    client.headers["Content-Type"] = "text/plain"
    resp_imp = client._make_request("PUT", f"/databases/name/{encoded_db}/import", data=csv_text)
    client.headers["Content-Type"] = "application/json"
    import_duration = time.time() - import_start
    
    if not resp_imp or resp_imp.status_code != 200:
        print(f"❌ Database Dump Import failed for: {database_fqn}")
        return export_duration, None
        
    return export_duration, import_duration

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python table_load_comparison.py <schema_fully_qualified_name>")
        print("Example: python table_load_comparison.py Enterprise_SE.CUSTOMERS.COLLATE_SE")
        sys.exit(1)

    schema_fqn = sys.argv[1]
    
    parts = schema_fqn.split('.')
    if len(parts) >= 2:
        database_fqn = f"{parts[0]}.{parts[1]}"
    else:
        database_fqn = schema_fqn

    client = OpenMetadataClient()
    
    print(f"🚀 Starting Benchmarks for Schema: {schema_fqn}")
    print(f"📦 Parent Database FQN: {database_fqn}")
    
    m1_exp, m1_imp = measure_individual_tables(client, schema_fqn)
    m2_exp, m2_imp = measure_schema_bulk(client, schema_fqn)
    m3_exp, m3_imp = measure_database_bulk(client, database_fqn)
    
    print("\n" + "="*70)
    print(f"{'METRIC COMPARISON':<38} | {'EXPORT TIME':<13} | {'IMPORT TIME':<13}")
    print("="*70)
    
    def format_time(t):
        return f"{t:.4f}s" if t is not None else "FAILED"
        
    print(f"{'1. Individual Table Loop':<38} | {format_time(m1_exp):<13} | {format_time(m1_imp):<13}")
    print(f"{'2. Bulk Database Schema Export':<38} | {format_time(m2_exp):<13} | {format_time(m2_imp):<13}")
    print(f"{'3. Full Database Schema Dump':<38} | {format_time(m3_exp):<13} | {format_time(m3_imp):<13}")
    print("-"*70)
    
    if m1_exp and m2_exp:
        print(f"💡 Bulk Schema Export is {m1_exp / m2_exp:.2f}x faster than Table Looping.")
    if m1_imp and m2_imp:
        print(f"💡 Bulk Schema Import is {m1_imp / m2_imp:.2f}x faster than Table Looping.")
    print("="*70)

if __name__ == "__main__":
    main()

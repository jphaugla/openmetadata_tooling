#!/usr/bin/env python3
import requests
import os
import sys
import json

BASE_URL = os.environ.get("API_BASE")
if not BASE_URL:
    print("❌ API_BASE environment variable not set. Run: source ~/.collate/setJson.sh")
    sys.exit(1)

# Default to your Enterprise_SE service
SERVICE_FQN = "Enterprise_SE"

def get_headers():
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN environment variable not set.")
        sys.exit(1)
    return {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

def list_all_tables_in_service(service_fqn):
    """Fetch all tables belonging to a specific service."""
    print(f"📡 Fetching all tables for service: {service_fqn}...")
    # Search for all tables where service name matches
    query = f"service.name:\"{service_fqn}\""
    url = f"{BASE_URL}/search/query?q={query}&index=table_search_index&size=200"
    res = requests.get(url, headers=get_headers())
    if res.status_code != 200:
        print(f"❌ Failed to search tables: {res.text}")
        return []
    
    hits = res.json().get("hits", {}).get("hits", [])
    return [hit["_source"] for hit in hits]

def clear_column_descriptions(table):
    """Patch the table to remove all column descriptions."""
    table_name = table["name"]
    table_id = table["id"]
    
    # We need the full table entity to see the columns
    full_table = requests.get(f"{BASE_URL}/tables/{table_id}", headers=get_headers()).json()
    columns = full_table.get("columns", [])
    
    if not columns:
        return

    # Prepare the PATCH
    headers = {**get_headers(), "Content-Type": "application/json-patch+json"}
    patch_ops = []
    
    for i, col in enumerate(columns):
        if col.get("description"):
            patch_ops.append({
                "op": "replace",
                "path": f"/columns/{i}/description",
                "value": ""
            })
    
    # Also clear table description if desired
    if full_table.get("description"):
        patch_ops.append({
            "op": "replace",
            "path": "/description",
            "value": ""
        })

    if not patch_ops:
        return

    print(f"  🧹 Clearing descriptions for {table_name}...")
    res = requests.patch(f"{BASE_URL}/tables/{table_id}", headers=headers, json=patch_ops)
    if res.status_code in [200, 201]:
        print(f"    ✅ Cleared.")
    else:
        print(f"    ❌ Failed: {res.text}")

def main():
    service_name = sys.argv[1] if len(sys.argv) > 1 else SERVICE_FQN
    tables = list_all_tables_in_service(service_name)
    
    if not tables:
        print(f"❌ No tables found for service {service_name}.")
        return

    print(f"📋 Found {len(tables)} tables. cleaning up...")
    
    for tbl in tables:
        clear_column_descriptions(tbl)

    print("\n✨ Metadata cleanup complete. Your service is back to its raw state.")

if __name__ == "__main__":
    main()

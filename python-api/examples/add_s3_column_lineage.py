#!/usr/bin/env python3
"""
Add column-level lineage between an S3 File (sub-container) and a Snowflake table.
Creates distinct container entities for each CSV file.

Usage:
    python add_s3_column_lineage.py <table_fqn> <cols> <file_name>
"""

import requests
import os
import sys
import json

BASE_URL = os.environ.get("API_BASE")
if not BASE_URL:
    print("❌ API_BASE environment variable not set. Run: source ~/.collate/setJson.sh")
    sys.exit(1)

# ── Configuration (Defaults) ──────────────────────────────────────────────────────
S3_PARENT_FQN     = "S3-Interchange.collate-snowflake-interchange-118146679784"
DEFAULT_TABLE     = "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS"
DEFAULT_COLUMNS   = ["ID", "FIRST_NAME", "LAST_NAME"]
DEFAULT_FILE      = "raw_customers_export.csv"
# ──────────────────────────────────────────────────────────────────────────────


def get_headers(patch=False):
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN environment variable not set. Run: source ~/.collate/setJson.sh")
        sys.exit(1)
    content_type = "application/json-patch+json" if patch else "application/json"
    return {"Authorization": f"Bearer {jwt}", "Content-Type": content_type}


def get_entity(entity_type, fqn, fields=None):
    """Fetch an entity by fully qualified name."""
    headers = get_headers()
    url = f"{BASE_URL}/{entity_type}/name/{fqn}?include=all"
    if fields:
        url += f"&fields={fields}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    return None


def get_or_create_file_container(parent, file_name, column_names):
    """Fetch existing or create a new child container for the CSV file."""
    # Quote the file name in the FQN if it contains a dot (Collate's standard convention)
    quoted_file_name = f'"{file_name}"' if "." in file_name else file_name
    child_fqn = f"{parent['fullyQualifiedName']}.{quoted_file_name}"
    child = get_entity("containers", child_fqn, fields="dataModel")
    
    # Prepare column objects
    cols = []
    for col in column_names:
        cols.append({
            "name": col,
            "dataType": "VARCHAR",
            "dataTypeDisplay": "VARCHAR"
        })

    if child:
        print(f"✅ Found existing file container: {file_name}")
        
        # Restore if deleted
        if child.get("deleted"):
            print(f"♻️  Restoring soft-deleted container: {file_name}")
            requests.put(f"{BASE_URL}/containers/restore", headers=get_headers(), json={"id": child["id"]})
            # Re-fetch after restore
            child = get_entity("containers", child["fullyQualifiedName"], fields="dataModel")

        # Patch data model if needed
        headers = get_headers(patch=True)
        display_name = f"{file_name} (Iceberg Table)"
        payload = [
            {
                "op": "add",
                "path": "/dataModel",
                "value": {"isPartitioned": False, "columns": cols}
            },
            {
                "op": "replace",
                "path": "/displayName",
                "value": display_name
            }
        ]
        res = requests.patch(f"{BASE_URL}/containers/{child['id']}", headers=headers, json=payload)
        if res.status_code in [200, 201]:
            return res.json()
        return child
    
    print(f"✨ Creating new file container: {file_name}")
    headers = get_headers()
    # Format the display name to look like an Iceberg table
    display_name = f"{file_name} (Iceberg Table)"
    
    payload = {
        "name": file_name,
        "displayName": display_name,
        "service": parent["service"]["name"],
        "parent": {"id": parent["id"], "type": "container"},
        "dataModel": {
            "isPartitioned": False,
            "columns": cols
        }
    }
    res = requests.post(f"{BASE_URL}/containers", headers=headers, json=payload)
    if res.status_code in [200, 201]:
        return res.json()
    else:
        print(f"❌ Failed to create container: HTTP {res.status_code} - {res.text}")
        sys.exit(1)


def push_column_lineage(container, table, column_names):
    """Push column-level lineage edge from S3 file container -> Snowflake table."""
    headers = get_headers()

    s3_cols = container.get("dataModel", {}).get("columns", [])
    s3_col_fqns = {c["name"]: c["fullyQualifiedName"] for c in s3_cols}

    tbl_cols = table.get("columns", [])
    tbl_col_fqns = {c["name"]: c["fullyQualifiedName"] for c in tbl_cols}

    columns_lineage = []
    for col_name in column_names:
        # Match case-insensitive or direct match? Tables usually uppercase, S3 might be mixed
        # Let's try to match intelligently
        s3_search = {k.upper(): v for k, v in s3_col_fqns.items()}
        tbl_search = {k.upper(): v for k, v in tbl_col_fqns.items()}
        
        name_up = col_name.upper()
        if name_up in s3_search and name_up in tbl_search:
            columns_lineage.append({
                "fromColumns": [s3_search[name_up]],
                "toColumn": tbl_search[name_up],
            })

    edge_payload = {
        "edge": {
            "fromEntity": {"id": container["id"], "type": "container"},
            "toEntity": {"id": table["id"], "type": "table"},
            "lineageDetails": {
                "columnsLineage": columns_lineage,
            },
        }
    }

    res = requests.put(f"{BASE_URL}/lineage", headers=headers, json=edge_payload)
    if res.status_code in [200, 201]:
        print(f"✅ Success! Lineage stored for {table['name']}.")
    else:
        print(f"❌ Failed to create lineage: {res.text}")


def main():
    # Allow arguments: python script.py <table_fqn> <comma_separated_cols> <file_name>
    target_table = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TABLE
    target_cols  = sys.argv[2].split(",") if len(sys.argv) > 2 else DEFAULT_COLUMNS
    target_file  = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_FILE

    print(f"🔍 Fetching Parent S3 Bucket: {S3_PARENT_FQN}")
    parent = get_entity("containers", S3_PARENT_FQN)
    if not parent:
        print("❌ Could not find parent bucket container.")
        return

    # Get/Create child container for the file
    file_container = get_or_create_file_container(parent, target_file, target_cols)
    
    # Re-fetch for updated FQNs
    file_container = get_entity("containers", file_container["fullyQualifiedName"], fields="dataModel")

    print(f"🔍 Fetching Snowflake table: {target_table}")
    table = get_entity("tables", target_table)
    if not table: return

    push_column_lineage(file_container, table, target_cols)


if __name__ == "__main__":
    main()


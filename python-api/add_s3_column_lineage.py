#!/usr/bin/env python3
"""
Add column-level lineage between an S3 Container and a Snowflake table.
This works around the OpenMetadata S3 agent Pydantic bug (BucketArn extra field)
that prevents the native agent from running and building this link automatically.

Usage:
    python add_s3_column_lineage.py

Requires:
    - TOKEN env var set (e.g. source ~/.collate/setJson.sh)
    - The S3 container and Snowflake table already exist in Collate
"""

import requests
import os
import sys
import json

BASE_URL = "https://jsonh.pov.getcollate.io/api/v1"

# ── Configuration ──────────────────────────────────────────────────────────────
S3_CONTAINER_FQN  = "S3-Interchange.collate-snowflake-interchange-118146679784"
SNOWFLAKE_TABLE_FQN = "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS"

# Columns that exist in BOTH the S3 CSV and the Snowflake table
COLUMN_NAMES = ["ID", "FIRST_NAME", "LAST_NAME"]
# ──────────────────────────────────────────────────────────────────────────────


def get_headers():
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN environment variable not set. Run: source ~/.collate/setJson.sh")
        sys.exit(1)
    return {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}


def get_entity(entity_type, fqn, fields=None):
    """Fetch an entity by fully qualified name."""
    headers = get_headers()
    url = f"{BASE_URL}/{entity_type}/name/{fqn}"
    if fields:
        url += f"?fields={fields}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"❌ Could not fetch {entity_type}/{fqn}: HTTP {res.status_code}")
        print(res.text)
        sys.exit(1)
    return res.json()


def patch_container_data_model(container_id, columns):
    """Use JSON Patch to add/replace the dataModel on the container."""
    headers = {**get_headers(), "Content-Type": "application/json-patch+json"}
    payload = [
        {
            "op": "add",
            "path": "/dataModel",
            "value": {
                "isPartitioned": False,
                "columns": [
                    {
                        "name": col,
                        "dataType": "INT" if col == "ID" else "VARCHAR",
                        "dataTypeDisplay": "INT" if col == "ID" else "VARCHAR",
                        "description": {
                            "ID": "Customer Identifier",
                            "FIRST_NAME": "First Name",
                            "LAST_NAME": "Last Name",
                        }.get(col, col),
                    }
                    for col in columns
                ],
            },
        }
    ]
    res = requests.patch(f"{BASE_URL}/containers/{container_id}", headers=headers, json=payload)
    if res.status_code in [200, 201]:
        print("✅ Patched dataModel onto S3 container.")
        return res.json()
    else:
        print(f"❌ Failed to patch container: HTTP {res.status_code}")
        print(res.text)
        sys.exit(1)


def push_column_lineage(container, table):
    """Push column-level lineage edge from S3 container -> Snowflake table."""
    headers = get_headers()

    # Build FQNs from stored container columns
    s3_cols = container.get("dataModel", {}).get("columns", [])
    s3_col_fqns = {c["name"]: c["fullyQualifiedName"] for c in s3_cols}

    tbl_cols = table.get("columns", [])
    tbl_col_fqns = {c["name"]: c["fullyQualifiedName"] for c in tbl_cols}

    columns_lineage = []
    for col_name in COLUMN_NAMES:
        if col_name in s3_col_fqns and col_name in tbl_col_fqns:
            columns_lineage.append(
                {
                    "fromColumns": [s3_col_fqns[col_name]],
                    "toColumn": tbl_col_fqns[col_name],
                }
            )
        else:
            print(f"⚠️  Column '{col_name}' not found in both entities, skipping.")

    print(f"🔗 Mapping {len(columns_lineage)} column(s):")
    for cl in columns_lineage:
        print(f"   {cl['fromColumns'][0]}  →  {cl['toColumn']}")

    edge_payload = {
        "edge": {
            "fromEntity": {"id": container["id"], "type": "container"},
            "toEntity": {"id": table["id"], "type": "table"},
            "lineageDetails": {
                "sqlQuery": "COPY INTO RAW_CUSTOMERS FROM @S3_STAGE",
                "columnsLineage": columns_lineage,
            },
        }
    }

    res = requests.put(f"{BASE_URL}/lineage", headers=headers, json=edge_payload)
    if res.status_code in [200, 201]:
        print("✅ SUCCESS! Column-level lineage edge stored.")
    else:
        print(f"❌ Failed to create lineage: HTTP {res.status_code}")
        print(res.text)
        sys.exit(1)


def main():
    print("🔍 Fetching S3 Container (with dataModel)...")
    container = get_entity("containers", S3_CONTAINER_FQN, fields="dataModel")

    # If the container has no columns (because native agent crashed), patch them in first
    if not container.get("dataModel") or not container["dataModel"].get("columns"):
        print("⚠️  No dataModel found on S3 container — patching columns in...")
        container = patch_container_data_model(container["id"], COLUMN_NAMES)
        # Re-fetch to get FQNs that Collate assigns after the patch
        print("🔍 Re-fetching S3 Container after patch...")
        container = get_entity("containers", S3_CONTAINER_FQN, fields="dataModel")
    else:
        print(f"✅ S3 Container already has {len(container['dataModel']['columns'])} column(s).")

    print("🔍 Fetching Snowflake table...")
    table = get_entity("tables", SNOWFLAKE_TABLE_FQN)

    push_column_lineage(container, table)


if __name__ == "__main__":
    main()

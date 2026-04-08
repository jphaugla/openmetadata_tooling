#!/usr/bin/env python3
"""
Restore S3 container and re-establish full lineage after soft-deletion.

Background:
    The Collate SaaS S3 Agent (v1.12.3) crashes due to a Pydantic validation error
    when AWS returns a 'BucketArn' field in the list_buckets() response.
    When the agent crashes, it soft-deletes containers that it couldn't discover,
    breaking the S3 -> Snowflake lineage in the catalog.

    Run this script after every failed S3 metadata agent run to restore the container
    and re-inject the column-level lineage.

Usage:
    source ~/.collate/setJson.sh
    python restore_s3_container.py

"""
import requests
import os
import sys

BASE_URL = "https://jsonh.pov.getcollate.io/api/v1"

# ── Configuration ──────────────────────────────────────────────────────────────
S3_SERVICE_FQN    = "S3-Interchange"
S3_BUCKET_NAME    = "collate-snowflake-interchange-118146679784"
S3_CONTAINER_FQN  = f"{S3_SERVICE_FQN}.{S3_BUCKET_NAME}"
SNOWFLAKE_TABLE_FQN = "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS"
COLUMN_NAMES      = ["ID", "FIRST_NAME", "LAST_NAME"]
# ──────────────────────────────────────────────────────────────────────────────


def headers(content_type="application/json"):
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN not set. Run: source ~/.collate/setJson.sh")
        sys.exit(1)
    return {"Authorization": f"Bearer {jwt}", "Content-Type": content_type}


def find_container(include_deleted=False):
    url = f"{BASE_URL}/containers/name/{S3_CONTAINER_FQN}"
    if include_deleted:
        url += "?include=deleted"
    res = requests.get(url, headers=headers())
    if res.status_code == 200:
        return res.json()
    return None


def restore_container(container_id):
    res = requests.put(f"{BASE_URL}/containers/restore", headers=headers(), json={"id": container_id})
    return res.status_code in [200, 201]


def patch_data_model(container_id):
    col_types = {"ID": "INT", "FIRST_NAME": "VARCHAR", "LAST_NAME": "VARCHAR"}
    col_descs = {"ID": "Customer Identifier", "FIRST_NAME": "First Name", "LAST_NAME": "Last Name"}
    payload = [{
        "op": "add",
        "path": "/dataModel",
        "value": {
            "isPartitioned": False,
            "columns": [
                {"name": c, "dataType": col_types[c], "dataTypeDisplay": col_types[c], "description": col_descs[c]}
                for c in COLUMN_NAMES
            ]
        }
    }]
    res = requests.patch(f"{BASE_URL}/containers/{container_id}", headers=headers("application/json-patch+json"), json=payload)
    return res.status_code in [200, 201]


def push_lineage(container, table):
    s3_fqns  = {c["name"]: c["fullyQualifiedName"] for c in container.get("dataModel", {}).get("columns", [])}
    tbl_fqns = {c["name"]: c["fullyQualifiedName"] for c in table.get("columns", [])}

    cols_lineage = [
        {"fromColumns": [s3_fqns[c]], "toColumn": tbl_fqns[c]}
        for c in COLUMN_NAMES if c in s3_fqns and c in tbl_fqns
    ]

    payload = {
        "edge": {
            "fromEntity": {"id": container["id"], "type": "container"},
            "toEntity":   {"id": table["id"],     "type": "table"},
            "lineageDetails": {
                "sqlQuery": "COPY INTO RAW_CUSTOMERS FROM @S3_STAGE",
                "columnsLineage": cols_lineage,
            }
        }
    }
    res = requests.put(f"{BASE_URL}/lineage", headers=headers(), json=payload)
    return res.status_code in [200, 201], len(cols_lineage)


def main():
    # 1. Try active container first
    print(f"🔍 Looking for active container: {S3_CONTAINER_FQN}")
    container = find_container()

    if container:
        print("✅ Container is already active.")
    else:
        # 2. Look for soft-deleted container
        print("⚠️  Not found. Checking soft-deleted containers...")
        container = find_container(include_deleted=True)
        if not container:
            print(f"❌ Container '{S3_CONTAINER_FQN}' not found even in deleted state.")
            print("   Run python-api/create_s3_container.py first.")
            sys.exit(1)
        print(f"   Found soft-deleted container (ID: {container['id']}). Restoring...")
        if restore_container(container["id"]):
            print("✅ Container restored!")
        else:
            print("❌ Failed to restore container.")
            sys.exit(1)

    # 3. Ensure dataModel / columns exist
    container = find_container()  # re-fetch fresh state
    if not container.get("dataModel") or not container["dataModel"].get("columns"):
        print("⚠️  No columns on container. Patching dataModel...")
        if patch_data_model(container["id"]):
            print("✅ dataModel patched.")
            # Re-fetch to get server-assigned FQNs on columns
            res = requests.get(f"{BASE_URL}/containers/name/{S3_CONTAINER_FQN}?fields=dataModel", headers=headers())
            container = res.json()
        else:
            print("❌ Failed to patch dataModel.")
            sys.exit(1)
    else:
        res = requests.get(f"{BASE_URL}/containers/name/{S3_CONTAINER_FQN}?fields=dataModel", headers=headers())
        container = res.json()
        print(f"✅ Container has {len(container['dataModel']['columns'])} column(s).")

    # 4. Fetch Snowflake table
    print(f"🔍 Fetching Snowflake table: {SNOWFLAKE_TABLE_FQN}")
    tbl_res = requests.get(f"{BASE_URL}/tables/name/{SNOWFLAKE_TABLE_FQN}", headers=headers())
    if tbl_res.status_code != 200:
        print(f"❌ Could not fetch table: {tbl_res.status_code}")
        sys.exit(1)
    table = tbl_res.json()

    # 5. Push lineage edge with column mapping
    print("🔗 Pushing column-level lineage edge...")
    ok, count = push_lineage(container, table)
    if ok:
        print(f"✅ SUCCESS! {count} column(s) mapped: {S3_CONTAINER_FQN} → {SNOWFLAKE_TABLE_FQN}")
    else:
        print("❌ Failed to push lineage.")
        sys.exit(1)


if __name__ == "__main__":
    main()

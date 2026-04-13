#!/usr/bin/env python3
import requests
import os
import sys

# Setup environment variables
BASE_URL = os.environ.get("API_BASE")
TOKEN = os.environ.get("TOKEN")

if not BASE_URL or not TOKEN:
    print("❌ Error: API_BASE and TOKEN environment variables must be set.")
    sys.exit(1)

BUCKET_FQN = "S3-Interchange.collate-snowflake-interchange-118146679784"
RAW_TABLES = [
    "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS",
    "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_ORDERS",
    "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_ORDER_ITEMS",
    "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_PRODUCTS"
]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def get_entity_id(entity_type, fqn):
    res = requests.get(f"{BASE_URL}/{entity_type}/name/{fqn}", headers=headers)
    if res.status_code == 200:
        return res.json()['id']
    return None

def delete_lineage_edge(from_id, from_type, to_id, to_type):
    url = f"{BASE_URL}/lineage/{from_type}/{from_id}/{to_type}/{to_id}"
    res = requests.delete(url, headers=headers)
    if res.status_code == 200:
        print(f"✅ Removed edge: {from_type}/{from_id} -> {to_type}/{to_id}")
    else:
        print(f"❌ Failed to remove edge: {res.status_code} - {res.text}")

def main():
    bucket_id = get_entity_id("containers", BUCKET_FQN)
    if not bucket_id:
        print(f"❌ Could not find bucket: {BUCKET_FQN}")
        sys.exit(1)

    print(f"🧹 Cleaning up duplicate lineage from bucket {BUCKET_FQN}...")
    for table_fqn in RAW_TABLES:
        table_id = get_entity_id("tables", table_fqn)
        if table_id:
            delete_lineage_edge(bucket_id, "container", table_id, "table")
        else:
            print(f"⚠️ Could not find table: {table_fqn}")

    print("\n✨ Buckets edges cleared! Refresh the lineage view.")

if __name__ == "__main__":
    main()

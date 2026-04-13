#!/usr/bin/env python3
import requests
import os
import sys

# Setup environment variables
BASE_URL = os.environ.get("API_BASE") # e.g., https://your-collate-url/api/v1
TOKEN = os.environ.get("TOKEN")

if not BASE_URL or not TOKEN:
    print("❌ Error: API_BASE and TOKEN environment variables must be set.")
    sys.exit(1)

# Fully Qualified Names (FQNs)
TARGET_TABLE = "Enterprise_SE.CUSTOMERS.COLLATE_SE.CUSTOMERS"
SOURCES_TO_REMOVE = [
    "Enterprise_SE.CUSTOMERS.COLLATE_SE.ORDERS",
    "Enterprise_SE.CUSTOMERS.COLLATE_SE.ORDER_ITEMS"
]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def delete_lineage_edge(from_fqn, to_fqn):
    """Deletes the lineage edge between two entities."""
    # First, we need to get the IDs for the FQNs
    def get_id(fqn):
        res = requests.get(f"{BASE_URL}/tables/name/{fqn}", headers=headers)
        if res.status_code == 200:
            return res.json()['id']
        return None

    from_id = get_id(from_fqn)
    to_id = get_id(to_fqn)

    if from_id and to_id:
        # Collate/OpenMetadata lineage deletion endpoint
        url = f"{BASE_URL}/lineage/table/{from_id}/table/{to_id}"
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Successfully removed lineage: {from_fqn} -> {to_fqn}")
        else:
            print(f"❌ Failed to remove {from_fqn}: {response.text}")
    else:
        print(f"⚠️ Could not find IDs for {from_fqn} or {to_fqn}")

def main():
    print(f"Starting manual lineage cleanup for {TARGET_TABLE}...\n")
    for source in SOURCES_TO_REMOVE:
        delete_lineage_edge(source, TARGET_TABLE)
    print("\n✨ Cleanup complete. Refresh your lineage view in Collate.")

if __name__ == "__main__":
    main()

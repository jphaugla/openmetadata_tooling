#!/usr/bin/env python3
import sys
import json
import urllib.parse
from om_client import OpenMetadataClient

def create_task(client, table_fqn, owner):
    """
    Creates a RequestDescription task for the given table and owner.
    """
    owner_id = owner.get("id")
    owner_type = owner.get("type")
    owner_name = owner.get("name")

    print(f"📝 Creating task for owner: {owner_name} ({owner_type}) on table: {table_fqn}...")

    # OpenMetadata task thread structure
    task_payload = {
        "message": f"Please add or review the description for table {table_fqn}.",
        "from": "admin",
        "about": f"<#E::table::{table_fqn}>",
        "type": "Task",
        "taskDetails": {
            "assignees": [{"id": owner_id, "type": owner_type}],
            "type": "RequestDescription"
        }
    }

    try:
        response = client._make_request("POST", "/feed", json=task_payload)
        
        if response is not None:
            if response.status_code in [200, 201]:
                print(f"✅ Task created successfully for {table_fqn}!")
                return True
            else:
                print(f"❌ Failed to create task for {table_fqn}. Status: {response.status_code}")
                print(f"   Response Body: {response.text}")
                return False
        else:
            print(f"❌ Failed to create task for {table_fqn}. Response is None (check om_client.py output).")
            return False
    except Exception as e:
        print(f"❌ Exception in create_task: {e}")
        return False

def main():
    tables = [
        "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_PRODUCTS",
        "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_ORDERS",
        "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS",
        "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_ORDER_ITEMS"
    ]

    client = OpenMetadataClient()

    for fqn in tables:
        print(f"\n🔍 Processing table: {fqn}")
        
        # 1. Fetch table metadata to get the owner
        encoded_fqn = urllib.parse.quote(fqn)
        url = f"/tables/name/{encoded_fqn}?fields=owners"
        
        response = client._make_request("GET", url)
        
        if not response or response.status_code != 200:
            status = response.status_code if response else "Unknown"
            print(f"❌ Error fetching table {fqn}. Status: {status}")
            continue

        table_data = response.json()
        owners = table_data.get("owners", [])

        if not owners:
            print(f"⚠️ No owners found for table {fqn}. Skipping task creation.")
            continue

        # In OpenMetadata, owners is a list. We'll create a task for the first owner found.
        # Usually, there's only one primary owner or one team.
        primary_owner = owners[0]
        create_task(client, fqn, primary_owner)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import requests
import os
import sys

BASE_URL = os.environ.get("API_BASE")
if not BASE_URL:
    print("❌ API_BASE environment variable not set. Run: source ~/.collate/setJson.sh")
    sys.exit(1)
SERVICE_NAME = "S3-Interchange"
BUCKET_NAME = "collate-snowflake-interchange-118146679784"
SNOWFLAKE_BASE_FQN = "Enterprise_SE.CUSTOMERS.COLLATE_SE"

def get_headers():
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN environment variable not set.")
        sys.exit(1)
    return {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

def main():
    headers = get_headers()
    
    # 1. KILL THE POISONED CONTAINER
    # We use a Search query to find the ID since the Name lookup is 500ing
    print(f"🕵️  Searching for poisoned container: {BUCKET_NAME}...")
    search_url = f"{BASE_URL}/search/query?q=name:\"{BUCKET_NAME}\"&index=container_search_index"
    search_res = requests.get(search_url, headers=headers).json()
    
    hits = search_res.get("hits", {}).get("hits", [])
    if not hits:
        print("ℹ️  No container found to delete. Proceeding to creation.")
    else:
        container_id = hits[0]["_source"]["id"]
        print(f"🗑️  Deleting poisoned container ID: {container_id}...")
        requests.delete(f"{BASE_URL}/containers/{container_id}?hardDelete=true", headers=headers)
        print("✅ Deleted.")

    # 2. CREATE A FRESH CLEAN CONTAINER
    print(f"📦 Creating fresh container: {BUCKET_NAME}...")
    # Fetch service first
    service = requests.get(f"{BASE_URL}/services/storageServices/name/{SERVICE_NAME}", headers=headers).json()
    
    payload = {
        "name": BUCKET_NAME,
        "displayName": BUCKET_NAME,
        "service": service["fullyQualifiedName"],
        "numberOfObjects": 1
    }
    create_res = requests.post(f"{BASE_URL}/containers", headers=headers, json=payload)
    if create_res.status_code not in [200, 201]:
        print(f"❌ Failed to create: {create_res.text}")
        return
    
    new_container = create_res.json()
    print(f"✅ Created New Container ID: {new_container['id']}")

    # 3. RUN THE SYNC
    print("🚀 Triggering full lineage sync...")
    script_path = os.path.join(os.path.dirname(__file__), "sync_all_lineage.py")
    # We need to update the ID in add_s3_column_lineage.py or just use the FQN now that it's clean
    os.system(f"python3 {script_path}")

if __name__ == "__main__":
    main()

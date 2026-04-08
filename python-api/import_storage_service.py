# python-api/import_storage_service.py
#!/usr/bin/env python3
import sys
import os
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python import_storage_service.py <service_name> [region]")
        print("Example: python import_storage_service.py S3-Interchange us-east-2")
        sys.exit(1)

    service_name = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-east-1"
    
    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    print(f"👤 Resolving owner for ID: {owner_id}...")
    user_data = client.get_user_by_id(owner_id)
    if not user_data or "name" not in user_data:
        print(f"❌ Error: Could not find user name for ID {owner_id}.")
        sys.exit(1)

    payload = {
        "name": service_name,
        "serviceType": "S3",
        "connection": {
            "config": {
                "type": "S3",
                "awsConfig": {
                    "awsRegion": region
                }
            }
        },
        "owners": [{"id": owner_id, "type": "user"}]
    }

    print(f"🚀 Importing S3 Storage Service: {service_name} ({region})...")
    response = client._make_request("POST", "/services/storageServices", json=payload)
    
    if response and response.status_code in [200, 201]:
        print(f"✅ Success! Created service ID: {response.json().get('id')}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else "No response"
        print(f"❌ Failed to create service. Status: {status}")
        print(f"      Response: {text}")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
import sys
import os
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python import_datalake_service.py <service_name> [region]")
        print("Example: python import_datalake_service.py S3-Datalake us-east-2")
        sys.exit(1)

    service_name = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-east-2"
    
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

    # Datalake Connection Schema (Corrected for 1.12.x bucket recognition)
    payload = {
        "name": service_name,
        "serviceType": "Datalake",
        "connection": {
            "config": {
                "type": "Datalake",
                "configSource": {
                    "securityConfig": {
                        "awsAccessKeyId": "AKIARXAQXIPUJQFNI6AU",
                        "awsSecretAccessKey": "secret:/jsonh-pov/storage/s3-interchange/awsconfig/awssecretaccesskey",
                        "awsRegion": region
                    }
                },
                "bucketName": "collate-snowflake-interchange-118146679784",
                "supportsMetadataExtraction": True
            }
        },
        "owners": [{"id": owner_id, "type": "user"}]
    }

    print(f"🚀 Creating Datalake Service: {service_name} ({region})...")
    response = client._make_request("POST", "/services/databaseServices", json=payload)
    
    if response and response.status_code in [200, 201]:
        print(f"✅ Success! Created Datalake service ID: {response.json().get('id')}")
        print(f"🔗 You can now run ingestion in Collate to discover your CSV files as tables.")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else "No response"
        print(f"❌ Failed to create service. Status: {status}")
        print(f"      Response: {text}")

if __name__ == "__main__":
    main()

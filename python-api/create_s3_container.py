#!/usr/bin/env python3
import sys
import os
import json
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python create_s3_container.py <service_name> <bucket_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    bucket_name = sys.argv[2]
    
    client = OpenMetadataClient()
    
    # 1. Get the Service (Just to verify it exists and get its FQN)
    print(f"🔍 Finding Storage Service: {service_name}...")
    response = client._make_request("GET", f"/services/storageServices/name/{service_name}?include=all")
    if response is None or response.status_code != 200:
        print(f"❌ Error: Could not find storage service '{service_name}'")
        return
    
    service_fqn = response.json().get("fullyQualifiedName", service_name)
    print(f"✅ Found Service FQN: {service_fqn}")
    
    # 2. Create the Container (The S3 Bucket node)
    print(f"📦 Manually creating S3 Container: {bucket_name}...")
    
    # In Collate 1.12.x, 'service' must be a String (The FQN), not an object
    payload = {
        "name": bucket_name,
        "displayName": bucket_name,
        "service": service_fqn,
        "numberOfObjects": 1,
        "size": 1403
    }
    
    res = client._make_request("POST", "/containers", json=payload)
    
    if res is not None:
        if res.status_code in [200, 201]:
            print(f"✅ Success! Container '{bucket_name}' created in Collate Metadata Catalog.")
            print(f"🔗 ID: {res.json().get('id')}")
        elif res.status_code == 409:
            print(f"ℹ️ Container '{bucket_name}' already exists in Collate.")
        else:
            print(f"❌ Failed to create container. Status: {res.status_code}")
            try:
                print(f"      Response: {json.dumps(res.json(), indent=2)}")
            except:
                print(f"      Response Text: {res.text}")
    else:
        print(f"❌ Fatal: No response from Collate API.")

if __name__ == "__main__":
    main()

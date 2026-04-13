#!/usr/bin/env python3
import sys
import os
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    owner_id = os.getenv("OWNER_ID")
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    print("🚀 Ensuring Pipeline Service exists...")
    
    # Check if Pipeline Service exists
    service_name = "Cockroach_to_Postgres_CDC"
    service_check = client._make_request("GET", f"/services/pipelineServices/name/{service_name}")
    
    if not service_check or service_check.status_code == 404:
        print(f"🏗️ Creating Pipeline Service: {service_name}...")
        service_payload = {
            "name": service_name,
            "serviceType": "CustomPipeline",
            "connection": {
                "config": {
                    "type": "CustomPipeline",
                    "sourceUrl": "cockroach://localhost:26257"
                }
            },
            "owners": [{"id": owner_id, "type": "user"}]
        }
        
        create_resp = client._make_request("POST", "/services/pipelineServices", json=service_payload)
        
        if create_resp and create_resp.status_code in [200, 201]:
            print("✅ Pipeline Service created.")
        else:
            print("❌ Failed to create Pipeline Service.")
            print(f"💬 Server Response: {create_resp.text if create_resp else 'Unknown Error'}")
            sys.exit(1)
    else:
        print("✅ Pipeline Service already exists.")

    print("🚀 Creating CDC Pipeline entity...")
    
    pipeline_payload = {
        "name": "movr_cdc",
        "displayName": "MovR Changefeed Sync",
        "description": "Real-time sync from CockroachDB to Postgres",
        "service": service_name
    }
    
    pipeline_resp = client._make_request("POST", "/pipelines", json=pipeline_payload)
    
    if pipeline_resp and pipeline_resp.status_code in [200, 201]:
        data = pipeline_resp.json()
        print("✅ Pipeline successfully created!")
        print(f"🆔 New Pipeline ID: {data.get('id')}")
        print(f"🔗 Pipeline Name: {data.get('name')}")
    else:
        print("❌ Failed to create pipeline.")
        print(f"💬 Server Response: {pipeline_resp.text if pipeline_resp else 'Unknown Error'}")
        sys.exit(1)

if __name__ == "__main__":
    main()

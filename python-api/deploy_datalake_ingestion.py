#!/usr/bin/env python3
import sys
import os
import json
from om_client import OpenMetadataClient

def main():
    service_name = "S3-Datalake"
    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    print(f"🔍 Finding Service: {service_name}...")
    service_id, service_type = client.get_service_id(service_name)
    
    if not service_id:
        print(f"❌ Error: Service '{service_name}' not found.")
        sys.exit(1)

    # Define the pipeline payload with the bucket name restriction and lowercase filter
    pipeline_payload = {
        "name": f"{service_name}_metadata",
        "displayName": f"{service_name} Metadata Ingestion",
        "pipelineType": "metadata",
        "sourceConfig": {
            "config": {
                "type": "DatalakeMetadata",
                "bucketNames": ["collate-snowflake-interchange-118146679784"],
                "databaseFilterPattern": {
                    "includes": ["collate-snowflake-interchange-118146679784"]
                },
                "schemaFilterPattern": {
                    "includes": [".*"]
                },
                "tableFilterPattern": {
                    "includes": ["raw_.*"]
                }
            }
        },
        "airflowConfig": {
            "pausePipeline": False,
            "startDate": "2026-04-14T00:00:00Z"
        },
        "service": {
            "id": service_id,
            "type": service_type
        },
        "owners": [{"id": owner_id, "type": "user"}]
    }

    # 1. Check for and Delete existing pipeline to ensure clean config
    print(f"🧹 Checking for existing pipeline: {pipeline_payload['name']}...")
    pipelines = client.get_pipelines_for_service(service_name)
    for p in pipelines:
        if p.get("name") == pipeline_payload["name"]:
            print(f"   🗑️ Deleting old pipeline (ID: {p.get('id')})...")
            client.delete_pipeline(p.get("id"))

    # 2. Create Pipeline
    print(f"🚀 Creating Filtered Ingestion Pipeline for {service_name}...")
    success, pipeline_id, response_text = client.create_pipeline(pipeline_payload)
    
    if not success:
        print(f"❌ Failed to create pipeline: {response_text}")
        sys.exit(1)

    # 2. Deploy Pipeline
    print(f"📡 Deploying Pipeline (ID: {pipeline_id})...")
    if client.deploy_pipeline(pipeline_id):
        print("   ✅ Deployment Successful!")
    else:
        print("   ❌ Deployment Failed.")
        sys.exit(1)

    # 3. Trigger Pipeline
    print(f"⚡ Triggering Pipeline run...")
    if client.trigger_pipeline(pipeline_id):
        print("   ✅ Pipeline Triggered! Scanning S3 now (filtered for 'raw_*').")
    else:
        print("   ❌ Trigger Failed.")

if __name__ == "__main__":
    main()

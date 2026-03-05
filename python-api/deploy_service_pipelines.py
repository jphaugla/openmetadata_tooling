#!/usr/bin/env python3
import sys
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python deploy_service_pipelines.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Identifying Service for: {service_name}...")
    service_id, service_type = client.get_service_id(service_name)
    
    if not service_id:
        print(f"❌ Error: Service '{service_name}' not found.")
        sys.exit(1)
        
    print(f"✅ Found {service_type}: {service_name}")
    print(f"🔍 Searching for Ingestion Pipelines tied to: {service_name}...")
    
    pipelines = client.get_pipelines_for_service(service_name)
    count = len(pipelines)
    
    if count == 0:
        print(f"⚠️ No pipelines found for service: {service_name}.")
        sys.exit(0)
        
    print(f"🚀 Found {count} pipelines. Starting deployment...")
    
    for pipeline in pipelines:
        p_name = pipeline.get("name")
        p_id = pipeline.get("id")
        p_type = pipeline.get("pipelineType")
        
        print("-" * 64)
        print(f"🛰️  Deploying Pipeline: {p_name} (ID: {p_id})")
        
        if client.deploy_pipeline(p_id):
             print("   ✅ Successfully Deployed!")
        else:
             print(f"   ⚠️ Deploy failed for {p_name}.")
             
    print("-" * 64)
    print(f"🏁 Done. Processed {count} pipelines for {service_name}.")

if __name__ == "__main__":
    main()

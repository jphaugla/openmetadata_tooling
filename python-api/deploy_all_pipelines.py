#!/usr/bin/env python3
import os
import sys
import glob
from om_client import OpenMetadataClient

def main():
    # Use the same JSON_DIR logic as other scripts
    json_dir_base = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    target_dir = os.path.join(json_dir_base, "pipelines")
    
    if not os.path.isdir(target_dir):
        print(f"❌ Error: Directory '{target_dir}' does not exist.")
        sys.exit(1)

    # Find all pipeline JSON files
    json_files = glob.glob(os.path.join(target_dir, "*_pipelines.json"))
    
    if not json_files:
        print(f"ℹ️ No pipeline JSON files found in {target_dir}")
        return

    client = OpenMetadataClient()
    
    # Track unique service names to avoid redundant lookups if multiple files exist (though unlikely)
    services_to_deploy = []
    for file_path in json_files:
        base_name = os.path.basename(file_path)
        service_name = base_name.replace("_pipelines.json", "")
        if service_name not in services_to_deploy:
            services_to_deploy.append(service_name)

    print(f"🚀 Found {len(services_to_deploy)} services with pipeline definitions. Deploying all...")

    total_deployed = 0
    for service_name in services_to_deploy:
        print("\n" + "=" * 64)
        print(f"🔍 Identifying Service: {service_name}...")
        service_id, service_type = client.get_service_id(service_name)
        
        if not service_id:
            print(f"   ⚠️ Warning: Service '{service_name}' not found in OpenMetadata. Skip.")
            continue
            
        print(f"   ✅ Found {service_type}: {service_name}")
        
        # Fetch pipelines currently in the system for this service
        pipelines = client.get_pipelines_for_service(service_name)
        count = len(pipelines)
        
        if count == 0:
            print(f"   ℹ️ No pipelines found in OM for service: {service_name}.")
            continue
            
        print(f"   🛰️  Found {count} pipelines. Starting deployment...")
        
        for pipeline in pipelines:
            p_name = pipeline.get("name")
            p_id = pipeline.get("id")
            
            print(f"      ➡️ Deploying: {p_name}")
            if client.deploy_pipeline(p_id):
                 print("         ✅ Success")
                 total_deployed += 1
            else:
                 print(f"         ❌ Failed")
                 
    print("\n" + "=" * 64)
    print(f"🏁 Bulk Deployment Complete. Total Pipelines Deployed: {total_deployed}")

if __name__ == "__main__":
    main()

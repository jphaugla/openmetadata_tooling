#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

# --- CONFIGURATION ---
RUN_DEPLOYMENT = False
# ---------------------

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python import_pipelines.py <pipelines_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not os.path.isfile(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    try:
        with open(input_file, "r") as f:
            pipelines_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        sys.exit(1)

    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    print(f"👤 Resolving name for Owner ID: {owner_id}...")
    user_data = client.get_user_by_id(owner_id)
    if not user_data or "name" not in user_data:
        print(f"❌ Error: Could not find user name for ID {owner_id}.")
        sys.exit(1)
        
    owner_name = user_data["name"]

    # Extract service name from filename (e.g., Cockroach_tpcc_pipelines.json -> Cockroach_tpcc)
    base_name = os.path.basename(input_file)
    service_name = base_name.replace("_pipelines.json", "")
    
    print(f"🔗 Resolving Service ID for {service_name}...")
    dest_svc_id, dest_svc_type = client.get_service_id(service_name)
    
    if not dest_svc_id:
        print(f"❌ Error: Service '{service_name}' not found as a Database or Search service. Import the service first.")
        sys.exit(1)
        
    print(f"✅ Found {dest_svc_type}: {service_name}")

    for agent in pipelines_data:
        p_name = agent.get("name")
        p_type = agent.get("pipelineType")
        
        print("-" * 64)
        print(f"🚀 Step 1: Importing {p_type} Agent: {p_name}")
        
        source_config = agent.get("sourceConfig", {})
        
        # Remove incompatible fields
        if "overrideLineage" in source_config.get("config", {}):
            del source_config["config"]["overrideLineage"]
            
        # Update owner config for metadata pipelines
        if p_type == "metadata":
            config = source_config.get("config", {})
            config["ownerConfig"] = {
                "default": owner_name,
                "service": owner_name,
                "database": owner_name,
                "enableInheritance": True
            }
            source_config["config"] = config
            
        clean_json = {
            "name": p_name,
            "pipelineType": p_type,
            "sourceConfig": source_config,
            "airflowConfig": agent.get("airflowConfig"),
            "loggerLevel": agent.get("loggerLevel", "INFO"),
            "service": {"id": dest_svc_id, "type": dest_svc_type},
            "owners": [{"id": owner_id, "type": "user"}]
        }
        
        # Optional fields
        for field in ["displayName", "description"]:
            if field in agent:
                clean_json[field] = agent[field]
                
        # Create the pipeline
        success, pipeline_id, raw_response = client.create_pipeline(clean_json)
        
        if success:
            print(f"   ✅ Created (ID: {pipeline_id})")
            
            if RUN_DEPLOYMENT:
                print("   🛰️  Step 2: Deploying to Orchestration...")
                if client.deploy_pipeline(pipeline_id):
                    print("   ✅ Successfully Deployed!")
                else:
                    print("   ⚠️ Deploy failed.")
            else:
                print("   ⏸️  Skipping Deployment (RUN_DEPLOYMENT=False).")
        else:
            print(f"   ❌ Failed to create: {raw_response}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Suite script to import all CockroachDB services and pipelines from JSON."""
import sys
import json
import os
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from om_client import OpenMetadataClient
from suite_delete_cockroach import main as delete_all

DATABASES = ["intro", "kv", "bank", "movr", "startrek", "tpcc", "ycsb"]

def main():
    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)
    
    # Validate owner
    print(f"🔍 Validating Owner ID: {owner_id}...")
    user_resp = client._make_request("GET", f"/users/{owner_id}")
    owner_name = None
    owner_type = None
    
    if user_resp and user_resp.status_code == 200:
        owner_name = user_resp.json().get("name")
        owner_type = "User"
    else:
        # Try team
        team_resp = client._make_request("GET", f"/teams/{owner_id}")
        if team_resp and team_resp.status_code == 200:
            owner_name = team_resp.json().get("name")
            owner_type = "Team"
            
    if not owner_name:
        print(f"❌ Error: Invalid OWNER_ID. Could not find User or Team with ID {owner_id}.")
        sys.exit(1)
        
    print(f"✅ Validated {owner_type}: {owner_name}")
    
    # 1. Pre-import cleanup
    print("🧹 Running Pre-import Cleanup...")
    delete_count = delete_all()
    
    print("🚀 Starting CockroachDB Suite Import...")
    print("-" * 42)
    
    if delete_count > 0:
        print("Pausing for 30 seconds to allow deletes to sync...")
        time.sleep(30)
        print("Continuing with import.")
    else:
        print("No services were deleted. Skipping 30 second sync wait.")
    
    json_dir = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    
    for db in DATABASES:
        service_name = f"Cockroach_{db}"
        print(f"Processing Service: {service_name}")
        
        # 2. Import Service Definition
        svc_file = os.path.join(json_dir, f"{service_name}.json")
        if os.path.isfile(svc_file):
            with open(svc_file, "r") as f:
                svc_data = json.load(f)
            
            create_payload = {
                "name": svc_data.get("name"),
                "serviceType": svc_data.get("serviceType"),
                "connection": svc_data.get("connection"),
                "owners": [{"id": owner_id, "type": "user"}]
            }
            resp = client._make_request("POST", "/services/databaseServices", json=create_payload)
            if resp and resp.status_code in [200, 201]:
                print(f"   ✅ Service imported (ID: {resp.json().get('id')})")
            else:
                print(f"   ❌ Service import failed: {resp.text if resp else 'Unknown'}")
        else:
            print(f"   ⚠️ {svc_file} not found. Skipping service import.")
            
        # 3. Import Pipelines
        pipelines_file = os.path.join(json_dir, f"{service_name}_pipelines.json")
        if os.path.isfile(pipelines_file):
            with open(pipelines_file, "r") as f:
                pipelines_data = json.load(f)
            
            # Get the destination service ID
            encoded = urllib.parse.quote(service_name)
            svc_check = client._make_request("GET", f"/services/databaseServices/name/{encoded}")
            if not svc_check or svc_check.status_code != 200:
                print(f"   ⚠️ Could not find destination service. Skipping pipeline import.")
                continue
                
            dest_svc_id = svc_check.json().get("id")
            
            for agent in pipelines_data:
                p_type = agent.get("pipelineType")
                p_name = agent.get("name")
                
                source_config = agent.get("sourceConfig", {})
                clean_json = {
                    "name": p_name,
                    "pipelineType": p_type,
                    "sourceConfig": source_config,
                    "airflowConfig": agent.get("airflowConfig"),
                    "loggerLevel": agent.get("loggerLevel", "INFO"),
                    "service": {"id": dest_svc_id, "type": "databaseService"},
                    "owners": [{"id": owner_id, "type": "user"}]
                }
                
                success, pid, raw = client.create_pipeline(clean_json)
                if success:
                    print(f"   ✅ Pipeline imported: {p_name} (ID: {pid})")
                else:
                    print(f"   ❌ Pipeline import failed: {p_name}: {raw}")
        else:
            print(f"   ⚠️ {pipelines_file} not found. Skipping pipeline import.")
            
        print("-" * 42)
    
    print("✅ Suite import complete.")

if __name__ == "__main__":
    main()

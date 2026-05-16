#!/usr/bin/env python3
import sys
import json
import os
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_service_pipeline_status.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Locating Service: {service_name}...")
    service_id, service_type = client.get_service_id(service_name)
    
    if not service_id:
        print(f"❌ Error: Service '{service_name}' not found as a Database or Search service.")
        sys.exit(1)
        
    print(f"✅ Found {service_type}: {service_name}")
    print(f"🔍 Fetching global pipeline orchestrator system status...")
    
    global_status_url = "/services/ingestionPipelines/status"
    global_status_resp = client._make_request("GET", global_status_url)
    if global_status_resp and global_status_resp.status_code == 200:
        print("⚙️  Orchestrator System Status:")
        print(json.dumps(global_status_resp.json(), indent=2))
    else:
        print("⚠️  Could not retrieve global orchestrator status matrix.")

    print(f"\n🔍 Searching for Ingestion Pipelines tied to: {service_name}...")
    pipelines = client.get_pipelines_for_service(service_name)
    count = len(pipelines)
    
    if count == 0:
        print(f"⚠️  No pipelines found for service: {service_name}.")
        sys.exit(0)
        
    print(f"✅ Found {count} pipelines. Gathering status records via pipelineStatuses field...\n")
    print("=" * 70)
    
    detailed_status_summary = []

    for pipeline in pipelines:
        pipeline_id = pipeline.get("id")
        pipeline_name = pipeline.get("name")
        pipeline_fqn = pipeline.get("fullyQualifiedName", "Unknown")  # Extracted FQN
        pipeline_type = pipeline.get("pipelineType", "Unknown")
        
        # Explicitly formatted console labels
        print(f"📋 Pipeline Name: {pipeline_name}")
        print(f"   🆔 ID: {pipeline_id}")
        print(f"   🌐 FQN (Fully Qualified Name): {pipeline_fqn}")
        print(f"   🗂️  Type: {pipeline_type}")
        
        # Requesting the pipeline entity with fields=pipelineStatuses
        status_url = f"/services/ingestionPipelines/{pipeline_id}?fields=pipelineStatuses"
        status_resp = client._make_request("GET", status_url)
        
        status_history = None
        if status_resp and status_resp.status_code == 200:
            # Extract history array from the pipeline entity object
            status_history = status_resp.json().get("pipelineStatuses", [])
            print("   📊 Execution Run Status History:")
            print(json.dumps(status_history, indent=2))
        else:
            status_code = status_resp.status_code if status_resp else "Unknown"
            print(f"   ❌ Error: Failed to fetch pipeline status. (Status: {status_code})")
            
        print("-" * 70)
        
        detailed_status_summary.append({
            "id": pipeline_id,
            "name": pipeline_name,
            "fullyQualifiedName": pipeline_fqn,  # Saved to JSON record
            "pipelineType": pipeline_type,
            "statusHistory": status_history
        })

    json_dir = os.path.join(os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json")), "pipeline_status")
    os.makedirs(json_dir, exist_ok=True)
    
    file_path = os.path.join(json_dir, f"{service_name}_fixed_status.json")
    with open(file_path, "w") as f:
        json.dump(detailed_status_summary, f, indent=2)
        
    print(f"💾 Detailed execution history successfully archived to {file_path}")

if __name__ == "__main__":
    main()

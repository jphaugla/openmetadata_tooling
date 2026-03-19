#!/usr/bin/env python3
import sys
import json
import os
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_pipelines.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Locating Service: {service_name}...")
    
    # Check if the service exists
    service_id, service_type = client.get_service_id(service_name)
    
    if not service_id:
        print(f"❌ Error: Service '{service_name}' not found as a Database or Search service.")
        sys.exit(1)
        
    print(f"✅ Found {service_type}: {service_name}")
    print(f"🔍 Searching for Ingestion Pipelines tied to: {service_name}...")
    
    pipelines = client.get_pipelines_for_service(service_name)
    count = len(pipelines)
    
    if count == 0:
        print(f"⚠️ No pipelines found for service: {service_name}.")
    else:
        print(f"✅ Found {count} pipelines (Metadata, Profiler, etc.).")
        
        json_dir = os.path.join(os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json")), "pipelines")
        os.makedirs(json_dir, exist_ok=True)
        
        file_path = os.path.join(json_dir, f"{service_name}_pipelines.json")
        
        with open(file_path, "w") as f:
            json.dump(pipelines, f, indent=2)
            
        print(f"💾 Saved to {file_path}")

if __name__ == "__main__":
    main()

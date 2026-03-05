#!/usr/bin/env python3
import sys
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python delete_pipeline_service.py <SERVICE_NAME>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🗑️  Preparing to HARD DELETE pipeline service: {service_name}")
    
    encoded_name = urllib.parse.quote(service_name)
    response = client._make_request("GET", f"/services/pipelineServices/name/{encoded_name}")
    
    service_id = None
    if response and response.status_code == 200:
        service_id = response.json().get("id")
        
    if service_id:
        print(f"✅ Found ID: {service_id}")
        delete_res = client._make_request("DELETE", f"/services/pipelineServices/{service_id}?hardDelete=true&recursive=true")
        
        if delete_res and delete_res.status_code == 200:
            print(f"💥 Pipeline Service {service_name} and its pipelines have been permanently deleted.")
        else:
            err = delete_res.json().get("message", delete_res.text) if delete_res else "Unknown HTTP Error"
            print(f"❌ Failed to delete: {err}")
    else:
        print(f"❌ Pipeline Service '{service_name}' not found. Nothing to delete.")
        sys.exit(1)

if __name__ == "__main__":
    main()

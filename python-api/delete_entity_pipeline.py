#!/usr/bin/env python3
import sys
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python delete_entity_pipeline.py <PIPELINE_NAME>")
        sys.exit(1)

    pipeline_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🗑️  Preparing to HARD DELETE pipeline entity: {pipeline_name}")
    
    encoded_name = urllib.parse.quote(pipeline_name)
    response = client._make_request("GET", f"/pipelines/name/{encoded_name}?include=all")
    
    pipeline_id = None
    if response and response.status_code == 200:
        pipeline_id = response.json().get("id")
        
    if pipeline_id:
        print(f"✅ Found ID: {pipeline_id}")
        delete_res = client._make_request("DELETE", f"/pipelines/{pipeline_id}?hardDelete=true")
        
        if delete_res and delete_res.status_code == 200:
            print(f"💥 Pipeline {pipeline_name} has been permanently deleted.")
        else:
            err = delete_res.json().get("message", delete_res.text) if delete_res else "Unknown HTTP Error"
            print(f"❌ Failed to delete: {err}")
    else:
        print(f"❌ Pipeline '{pipeline_name}' not found. Nothing to delete.")
        sys.exit(1)

if __name__ == "__main__":
    main()

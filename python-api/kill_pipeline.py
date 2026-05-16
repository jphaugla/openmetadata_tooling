#!/usr/bin/env python3
import sys
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python kill_pipeline.py <pipeline_name_or_fqn>")
        sys.exit(1)

    pipeline_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Finding Pipeline ID for: {pipeline_name}...")
    
    encoded_name = urllib.parse.quote(pipeline_name)
    response = client._make_request("GET", f"/services/ingestionPipelines/name/{encoded_name}")
    
    pipeline_id = None
    if response and response.status_code == 200:
        pipeline_id = response.json().get("id")
    else:
        print("❓ Not found by exact name/FQN. Searching via list...")
        list_response = client._make_request("GET", "/services/ingestionPipelines?limit=1000")
        
        if list_response and list_response.status_code == 200:
            pipelines = list_response.json().get("data", [])
            for p in pipelines:
                if p.get("name") == pipeline_name or p.get("fullyQualifiedName") == pipeline_name:
                    pipeline_id = p.get("id")
                    break
                    
    if not pipeline_id:
        print(f"❌ Error: Could not find pipeline '{pipeline_name}'.")
        sys.exit(1)
        
    print(f"🎯 Found Pipeline ID: {pipeline_id}")
    print("💀 Sending KILL signal...")
    
    kill_response = client._make_request("POST", f"/services/ingestionPipelines/kill/{pipeline_id}")
    
    if kill_response is not None and kill_response.status_code == 200:
        print("✅ Kill signal sent successfully. It may take a few moments for the status to update in the UI.")
    else:
        err = "Unknown HTTP Error"
        if kill_response is not None:
            try:
                err = kill_response.json().get("message", kill_response.text)
            except Exception:
                err = kill_response.text
        print("⚠️  Kill operation reported a problem.")
        print(f"   Message: {err}")
if __name__ == "__main__":
    main()

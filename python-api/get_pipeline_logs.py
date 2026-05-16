#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("❌ Usage: python get_pipeline_logs.py <pipeline_id_or_fqn> [run_id]")
        print("💡 Hint: Pass the database ID entity GUID.")
        sys.exit(1)

    pipeline_input = sys.argv[1]
    user_run_id = sys.argv[2] if len(sys.argv) == 3 else "last"
    
    client = OpenMetadataClient()
    
    print(f"🔍 Resolving Ingestion Pipeline and fetching execution history: {pipeline_input}...")
    pipeline_data = None
    
    id_url = f"/services/ingestionPipelines/{pipeline_input}?fields=pipelineStatuses"
    id_resp = client._make_request("GET", id_url)
    
    if id_resp is not None and id_resp.status_code == 200:
        pipeline_data = id_resp.json()
    else:
        encoded_input = urllib.parse.quote(pipeline_input)
        name_url = f"/services/ingestionPipelines/name/{encoded_input}?fields=pipelineStatuses"
        name_resp = client._make_request("GET", name_url)
        if name_resp is not None and name_resp.status_code == 200:
            pipeline_data = name_resp.json()

    if not pipeline_data:
        print(f"❌ Error: Ingestion Pipeline '{pipeline_input}' could not be located.")
        sys.exit(1)
        
    pipeline_id = pipeline_data.get("id")
    pipeline_fqn = pipeline_data.get("fullyQualifiedName")
    print(f"✅ Resolved Pipeline ID: {pipeline_id}")
    print(f"✅ Resolved Pipeline FQN: {pipeline_fqn}")

    target_run_id = None
    if user_run_id != "last":
        target_run_id = user_run_id
    else:
        statuses = pipeline_data.get("pipelineStatuses", [])
        if isinstance(statuses, list) and len(statuses) > 0:
            target_run_id = statuses[0].get("runId")
        elif isinstance(statuses, dict):
            target_run_id = statuses.get("runId")
            
    if not target_run_id:
        print("⚠️  Warning: No recent execution runId found in pipeline history. Defaulting to 'last'.")
        target_run_id = "last"
        
    print(f"🚀 Fetching logs from orchestrator for runId: {target_run_id}...")
    
    encoded_fqn = urllib.parse.quote(pipeline_fqn)
    
    # Use the specific top-level FQN route that yielded a successful 200 connection
    log_url = f"/services/ingestionPipelines/logs/{encoded_fqn}?runId={target_run_id}"
    response = client._make_request("GET", log_url)
    
    if response is not None and response.status_code == 200:
        # AUTOMATED STEP RESOLUTION FOR ARGO ORCHESTRATORS
        try:
            payload = response.json()
            if isinstance(payload, dict) and "runs" in payload and len(payload["runs"]) > 0:
                step_run_id = payload["runs"][0]
                print(f"📌 Argo step execution detected. Auto-resolving logs for pod node step: {step_run_id}...")
                
                step_url = f"/services/ingestionPipelines/logs/{encoded_fqn}?runId={step_run_id}"
                step_response = client._make_request("GET", step_url)
                if step_response is not None and step_response.status_code == 200:
                    response = step_response
        except Exception:
            pass  # Fall back to printing raw text if it's already a text log stream
            
        json_dir = os.path.join(
            os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json")), 
            "ingestionPipelineLogs"
        )
        os.makedirs(json_dir, exist_ok=True)
        
        safe_filename = pipeline_fqn.replace(".", "_")
        file_path = os.path.join(json_dir, f"{safe_filename}_{target_run_id}.log")
        
        with open(file_path, "w") as f:
            try:
                # Format nicely if json, otherwise dump flat text logs directly
                json.dump(response.json(), f, indent=2)
            except Exception:
                f.write(response.text)
            
        print(f"💾 Success! Saved resolved text logs to {file_path}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: Logs could not be fetched. (Status: {status})")
        print(text)
        sys.exit(1)

if __name__ == "__main__":
    main()

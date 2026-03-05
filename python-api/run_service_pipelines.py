#!/usr/bin/env python3
import sys
import time
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python run_service_pipelines.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Locating pipelines for Service: {service_name}...")
    pipelines = client.get_pipelines_for_service(service_name)
    count = len(pipelines)
    
    if count == 0:
        print(f"⚠️ No pipelines found for service: {service_name}.")
        sys.exit(0)
        
    metadata_pipelines = [p for p in pipelines if p.get("pipelineType") == "metadata"]
    other_pipelines = [p for p in pipelines if p.get("pipelineType") != "metadata"]
    
    if not metadata_pipelines:
        print(f"❌ Error: No Metadata pipeline found for {service_name}. Metadata is required first.")
        sys.exit(1)
        
    m_pipeline = metadata_pipelines[0]
    m_id = m_pipeline.get("id")
    m_name = m_pipeline.get("name")
    
    print(f"🚀 Step 1: Triggering Metadata Pipeline: {m_name} (ID: {m_id})...")
    
    if not client.trigger_pipeline(m_id):
        print(f"❌ Failed to trigger Metadata pipeline.")
        sys.exit(1)
        
    # Poll for completion
    print("⏳ Waiting for Metadata Pipeline to complete (check every 15s)...")
    max_retries = 80 # 20 minutes
    status = "running"
    
    for attempt in range(1, max_retries + 1):
        time.sleep(15)
        
        # We need specific fields to check status
        response = client._make_request("GET", f"/services/ingestionPipelines/{m_id}?fields=pipelineStatuses")
        
        if response and response.status_code == 200:
            data = response.json()
            latest_run = data.get("pipelineStatuses")
            status = latest_run.get("pipelineState", "running").lower() if latest_run else "running"
        else:
            status = "running"
            
        print(f"   [Attempt {attempt}] Current Status: {status}")
        
        if status == "success":
            print("✅ Metadata Pipeline Completed Successfully!")
            break
        elif status in ["failed", "partialsuccess"]:
            print(f"❌ Metadata Pipeline ended with state: {status}. Aborting subsequent pipelines.")
            if response and latest_run:
                error_msg = latest_run.get("error")
                if error_msg:
                    print(f"   Error Detail: {error_msg}")
            sys.exit(1)
        elif status not in ["running", "queued", "null"]:
            print(f"⚠️  Metadata Pipeline ended with unexpected state: {status}. Aborting.")
            sys.exit(1)
            
        if attempt == max_retries:
            print("❌ Timeout: Metadata pipeline did not complete within 20 minutes.")
            sys.exit(1)
            
    # Trigger dependents
    if not other_pipelines:
        print("ℹ️ No other pipelines found. Process complete.")
        sys.exit(0)
        
    print("🚀 Step 2: Triggering dependent pipelines...")
    for p in other_pipelines:
        p_name = p.get("name")
        p_id = p.get("id")
        p_type = p.get("pipelineType")
        
        print(f"   🛰️  Triggering {p_type}: {p_name}...")
        if client.trigger_pipeline(p_id):
            print("      ✅ Triggered successfully.")
        else:
            print("      ❌ Failed to trigger.")
            
    print(f"🏁 All pipelines for {service_name} have been triggered successfully.")

if __name__ == "__main__":
    main()

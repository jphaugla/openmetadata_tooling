#!/usr/bin/env python3
"""Suite script to run all CockroachDB service pipelines in sequence."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from om_client import OpenMetadataClient

DATABASES = ["intro", "kv", "bank", "movr", "startrek", "tpcc", "ycsb"]

def run_service_pipelines(client, service_name):
    """Orchestrates Metadata-first, then triggers dependents. Returns True on success."""
    pipelines = client.get_pipelines_for_service(service_name)
    
    if not pipelines:
        print(f"   ⚠️ No pipelines found for {service_name}.")
        return True
    
    metadata_pipelines = [p for p in pipelines if p.get("pipelineType") == "metadata"]
    other_pipelines = [p for p in pipelines if p.get("pipelineType") != "metadata"]
    
    if not metadata_pipelines:
        print(f"   ❌ No Metadata pipeline found for {service_name}.")
        return False
    
    m_pipeline = metadata_pipelines[0]
    m_id = m_pipeline.get("id")
    m_name = m_pipeline.get("name")
    
    print(f"   🚀 Triggering Metadata: {m_name}...")
    if not client.trigger_pipeline(m_id):
        print("   ❌ Failed to trigger Metadata pipeline.")
        return False
    
    print("   ⏳ Waiting for Metadata to complete...")
    for attempt in range(1, 81):
        time.sleep(15)
        status_resp = client._make_request("GET", f"/services/ingestionPipelines/{m_id}?fields=pipelineStatuses")
        status = "running"
        if status_resp and status_resp.status_code == 200:
            latest = status_resp.json().get("pipelineStatuses")
            status = latest.get("pipelineState", "running").lower() if latest else "running"
        
        print(f"   [Attempt {attempt}] Status: {status}")
        
        if status == "success":
            print("   ✅ Metadata Pipeline complete!")
            break
        elif status in ["failed", "partialsuccess"]:
            print(f"   ❌ Metadata Pipeline ended with: {status}")
            return False
        elif attempt == 80:
            print("   ❌ Timeout waiting for Metadata Pipeline.")
            return False
    
    # Trigger dependents
    for p in other_pipelines:
        p_type = p.get("pipelineType")
        p_name = p.get("name")
        p_id = p.get("id")
        
        print(f"   🛰️  Triggering {p_type}: {p_name}...")
        if client.trigger_pipeline(p_id):
            print("      ✅ Triggered.")
        else:
            print("      ❌ Failed to trigger.")
    
    return True

def main():
    client = OpenMetadataClient()
    
    print("🚀 Starting Full Pipeline Execution for CockroachDB Suite...")
    print("-" * 56)
    
    for db in DATABASES:
        service_name = f"Cockroach_{db}"
        print(f"📦 Service: {service_name}")
        
        run_service_pipelines(client, service_name)
        
        print("-" * 56)
    
    print("✅ All CockroachDB suite pipelines have been executed.")

if __name__ == "__main__":
    main()

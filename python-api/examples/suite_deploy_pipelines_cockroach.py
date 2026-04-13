#!/usr/bin/env python3
"""Suite script to deploy all CockroachDB service pipelines."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from om_client import OpenMetadataClient

DATABASES = ["intro", "kv", "bank", "movr", "startrek", "tpcc", "ycsb"]

def main():
    client = OpenMetadataClient()
    
    print("🚀 Starting Pipeline Deployment for CockroachDB Suite...")
    print("-" * 56)
    
    for db in DATABASES:
        service_name = f"Cockroach_{db}"
        print(f"📦 Service: {service_name}")
        
        pipelines = client.get_pipelines_for_service(service_name)
        
        if not pipelines:
            print(f"   ⚠️ No pipelines found for {service_name}.")
        
        for p in pipelines:
            p_name = p.get("name")
            p_id = p.get("id")
            p_type = p.get("pipelineType")
            
            print(f"   🛰️  Deploying: {p_name} ({p_type})...")
            if client.deploy_pipeline(p_id):
                print("      ✅ Deployed.")
            else:
                print("      ❌ Deploy failed.")
                
        print("-" * 56)
    
    print("✅ All CockroachDB suite pipelines processed.")

if __name__ == "__main__":
    main()

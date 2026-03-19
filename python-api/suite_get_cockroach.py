#!/usr/bin/env python3
"""Suite script to export (get) all CockroachDB services and pipelines to JSON."""
import sys
import json
import os
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from om_client import OpenMetadataClient

DATABASES = ["intro", "kv", "bank", "movr", "startrek", "tpcc", "ycsb"]

def main():
    client = OpenMetadataClient()
    json_dir = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    os.makedirs(json_dir, exist_ok=True)
    
    print("🚀 Starting CockroachDB Suite Export...")
    print("-" * 42)
    
    for db in DATABASES:
        service_name = f"Cockroach_{db}"
        print(f"Processing Service: {service_name}")
        
        # 1. Export Service Definition
        encoded_name = urllib.parse.quote(service_name)
        svc_resp = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
        if svc_resp and svc_resp.status_code == 200:
            svc_dir = os.path.join(json_dir, "databaseService")
            os.makedirs(svc_dir, exist_ok=True)
            file_path = os.path.join(svc_dir, f"{service_name}.json")
            with open(file_path, "w") as f:
                json.dump(svc_resp.json(), f, indent=2)
            print(f"   ✅ Service saved to {file_path}")
        else:
            print(f"   ⚠️ Service '{service_name}' not found. Skipping service export.")
            
        # 2. Export Pipelines
        pipelines = client.get_pipelines_for_service(service_name)
        if pipelines:
            p_dir = os.path.join(json_dir, "pipelines")
            os.makedirs(p_dir, exist_ok=True)
            file_path = os.path.join(p_dir, f"{service_name}_pipelines.json")
            with open(file_path, "w") as f:
                json.dump(pipelines, f, indent=2)
            print(f"   ✅ {len(pipelines)} pipeline(s) saved to {file_path}")
        else:
            print(f"   ⚠️ No pipelines found for '{service_name}'. Skipping pipeline export.")
            
        print("-" * 42)
    
    print("✅ Suite export complete.")

if __name__ == "__main__":
    main()

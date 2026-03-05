#!/usr/bin/env python3
"""Suite script to delete all CockroachDB services and their pipelines."""
import sys
import time
import os
import urllib.parse

# Add parent path so we can import other suite modules
sys.path.insert(0, os.path.dirname(__file__))
from om_client import OpenMetadataClient

DATABASES = ["intro", "kv", "bank", "movr", "startrek", "tpcc", "ycsb"]

def delete_service(client, service_name):
    encoded_name = urllib.parse.quote(service_name)
    response = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
    if response and response.status_code == 200:
        service_id = response.json().get("id")
        del_res = client._make_request("DELETE", f"/services/databaseServices/{service_id}?hardDelete=true&recursive=true")
        return del_res is not None and del_res.status_code == 200
    return False

def delete_pipelines(client, service_name):
    pipelines = client.get_pipelines_for_service(service_name)
    for p in pipelines:
        client.delete_pipeline(p["id"])

def main():
    client = OpenMetadataClient()
    delete_count = 0
    
    print("🧹 Starting CockroachDB Suite Cleanup...")
    print("-" * 42)
    
    for db in DATABASES:
        service_name = f"Cockroach_{db}"
        
        # 1. Delete Pipelines First (Clean slate)
        print(f"🗑️  Deleting pipelines for: {service_name}...")
        delete_pipelines(client, service_name)
        
        # 2. Delete the Service
        print(f"🗑️  Deleting service: {service_name}...")
        if delete_service(client, service_name):
            print("   ✅ Deleted.")
            delete_count += 1
        else:
            print("   ⚠️ Service not found or already deleted.")
            
        print("-" * 42)
    
    print(f"TOTAL_DELETED={delete_count}")
    print("✅ Suite cleanup complete.")
    
    return delete_count

if __name__ == "__main__":
    main()

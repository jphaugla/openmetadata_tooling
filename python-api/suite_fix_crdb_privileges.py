#!/usr/bin/env python3
"""Suite script to patch allow_unsafe_internals=true for all CockroachDB services."""
import sys
import os
import urllib.parse
import requests as req_lib

sys.path.insert(0, os.path.dirname(__file__))
from om_client import OpenMetadataClient

DATABASES = ["intro", "kv", "bank", "movr", "startrek", "tpcc", "ycsb"]

def patch_crdb_service(client, service_name):
    encoded_name = urllib.parse.quote(service_name)
    response = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
    if not response or response.status_code != 200:
        print(f"   ❌ Service '{service_name}' not found.")
        return False
    
    service_id = response.json().get("id")
    patch_payload = [{"op": "add", "path": "/connection/config/connectionOptions/options", "value": "-callow_unsafe_internals=true"}]
    
    headers = client.headers.copy()
    headers["Content-Type"] = "application/json-patch+json"
    
    patch_url = f"{client.api_base}/services/databaseServices/{service_id}"
    patch_resp = req_lib.patch(patch_url, headers=headers, json=patch_payload)
    
    if patch_resp.status_code == 200:
        opts = patch_resp.json().get("connection", {}).get("config", {}).get("connectionOptions", {}).get("options")
        if opts == "-callow_unsafe_internals=true":
            print(f"   ✅ Patched {service_name}")
            return True
    
    print(f"   ❌ Failed to patch {service_name}: {patch_resp.text}")
    return False

def main():
    client = OpenMetadataClient()
    
    print("🚀 Starting Privilege Fix for CockroachDB Suite...")
    print("🛠️  Adding allow_unsafe_internals=true to connection options...")
    print("-" * 56)
    
    for db in DATABASES:
        service_name = f"Cockroach_{db}"
        print(f"📦 Processing: {service_name}")
        patch_crdb_service(client, service_name)
        print("-" * 56)
    
    print("✅ All existing services patched.")

if __name__ == "__main__":
    main()

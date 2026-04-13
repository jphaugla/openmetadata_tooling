#!/usr/bin/env python3
"""Suite script to update hostPort for all CockroachDB services."""
import sys
import os
import urllib.parse
import requests as req_lib

sys.path.insert(0, os.path.dirname(__file__))
from om_client import OpenMetadataClient

DATABASES = ["intro", "kv", "bank", "movr", "startrek", "tpcc", "ycsb"]

def update_host_port(client, service_name, new_host_port):
    encoded_name = urllib.parse.quote(service_name)
    response = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
    if not response or response.status_code != 200:
        print(f"   ❌ Service '{service_name}' not found.")
        return False
    
    service_id = response.json().get("id")
    patch_payload = [{"op": "replace", "path": "/connection/config/hostPort", "value": new_host_port}]
    
    headers = client.headers.copy()
    headers["Content-Type"] = "application/json-patch+json"
    
    patch_url = f"{client.api_base}/services/databaseServices/{service_id}"
    patch_resp = req_lib.patch(patch_url, headers=headers, json=patch_payload)
    
    if patch_resp.status_code == 200:
        updated = patch_resp.json().get("connection", {}).get("config", {}).get("hostPort")
        if updated == new_host_port:
            print(f"   ✅ Updated {service_name} to {new_host_port}")
            return True
    
    print(f"   ❌ Failed to update {service_name}: {patch_resp.text}")
    return False

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python suite_update_host_port_cockroach.py <new_host:port>")
        sys.exit(1)
    
    new_host_port = sys.argv[1]
    client = OpenMetadataClient()
    
    print("🚀 Starting CockroachDB Suite Host/Port Update...")
    print(f"📡 Target Host/Port: {new_host_port}")
    print("-" * 42)
    
    for db in DATABASES:
        service_name = f"Cockroach_{db}"
        print(f"🔄 Updating Service: {service_name}")
        update_host_port(client, service_name, new_host_port)
        print("-" * 42)
    
    print("✅ Suite update complete.")

if __name__ == "__main__":
    main()

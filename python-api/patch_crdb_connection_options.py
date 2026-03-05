#!/usr/bin/env python3
import sys
import json
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python patch_crdb_connection_options.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Looking up ID for service: {service_name}...")
    encoded_name = urllib.parse.quote(service_name)
    response = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
    
    service_id = None
    if response and response.status_code == 200:
        service_id = response.json().get("id")
        
    if not service_id:
        print(f"❌ Error: Could not find service with name '{service_name}'.")
        sys.exit(1)

    # 2. Prepare JSON Patch
    # A single try to add the correct options parameter
    patch_payload = [
        {
            "op": "add",
            "path": "/connection/config/connectionOptions/options",
            "value": "-callow_unsafe_internals=true"
        }
    ]
    
    # Ideally we'd remove the 'allow_unsafe_internals' boolean flag if it exists, but JSON Patch 
    # 'remove' operation throws an error if the path doesn't exist, failing the entire transaction.
    # Therefore, we just overwrite/append the 'options' string which works perfectly.

    print(f"📡 Patching service '{service_name}' (ID: {service_id}) with allow_unsafe_internals=true...")
    
    headers = client.headers.copy()
    headers["Content-Type"] = "application/json-patch+json"
    
    patch_url = f"{client.api_base}/services/databaseServices/{service_id}"
    
    import requests
    try:
        patch_resp = requests.patch(patch_url, headers=headers, json=patch_payload)
        
        if patch_resp.status_code == 200:
            data = patch_resp.json()
            options = data.get("connection", {}).get("config", {}).get("connectionOptions", {}).get("options")
            
            if options == "-callow_unsafe_internals=true":
                print(f"✅ Successfully patched {service_name}")
            else:
                 print("⚠️ PATCH succeeded but 'options' did not match expected value.")
        else:
             print("❌ Failed to patch service.")
             print(f"💬 Server Response: {patch_resp.text}")
             sys.exit(1)
             
    except Exception as e:
        print(f"❌ Network error during PATCH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

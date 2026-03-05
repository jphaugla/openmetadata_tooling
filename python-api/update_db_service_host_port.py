#!/usr/bin/env python3
import sys
import json
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 3:
        print("❌ Usage: python update_db_service_host_port.py <service_name> <new_host:port>")
        sys.exit(1)

    service_name = sys.argv[1]
    new_host_port = sys.argv[2]
    
    client = OpenMetadataClient()
    
    # 1. Get Service ID
    print(f"🔍 Looking up ID for service: {service_name}...")
    encoded_name = urllib.parse.quote(service_name)
    response = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
    
    service_id = None
    if response and response.status_code == 200:
        service_id = response.json().get("id")
        
    if not service_id:
        print(f"❌ Error: Could not find service with name '{service_name}'.")
        sys.exit(1)
        
    print(f"🆔 Found Service ID: {service_id}")
    
    # 2. Prepare JSON Patch
    patch_payload = [{
        "op": "replace",
        "path": "/connection/config/hostPort",
        "value": new_host_port
    }]
    
    # 3. Execute PATCH
    print(f"📡 Sending PATCH request to update hostPort to: {new_host_port}...")
    
    # Use direct requests call because om_client doesn't have a generic patch_service method yet
    headers = client.headers.copy()
    headers["Content-Type"] = "application/json-patch+json"
    
    patch_url = f"{client.api_base}/services/databaseServices/{service_id}"
    
    import requests
    try:
        patch_resp = requests.patch(patch_url, headers=headers, json=patch_payload)
        
        if patch_resp.status_code == 200:
            updated_port = patch_resp.json().get("connection", {}).get("config", {}).get("hostPort")
            if updated_port == new_host_port:
                print(f"✅ Successfully updated hostPort for '{service_name}' to: {updated_port}")
            else:
                print("⚠️ PATCH succeeded but port does not match expected value.")
        else:
            print("❌ Failed to update service.")
            print(f"💬 Server Response: {patch_resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Network error during PATCH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

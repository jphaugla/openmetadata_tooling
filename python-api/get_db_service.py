#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_db_service.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    
    # URL Encoding handles spaces gracefully
    encoded_name = urllib.parse.quote(service_name)
    
    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Database Service: {service_name}...")
    
    # We use _make_request directly here because we want the full payload to save
    response = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
    
    if response and response.status_code == 200:
        json_dir = os.path.join(os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json")), "databaseService")
        os.makedirs(json_dir, exist_ok=True)
        
        file_path = os.path.join(json_dir, f"{service_name}.json")
        
        with open(file_path, "w") as f:
            json.dump(response.json(), f, indent=2)
            
        print(f"✅ Success! Saved to {file_path}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: Service '{service_name}' not found. (Status: {status})")
        print(text)
        sys.exit(1)

if __name__ == "__main__":
    main()

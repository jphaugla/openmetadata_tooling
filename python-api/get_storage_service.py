#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_storage_service.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    
    # URL Encoding handles spaces gracefully
    encoded_name = urllib.parse.quote(service_name)
    
    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Storage Service: {service_name}...")
    
    # We use _make_request directly here because we want the full payload to save
    # Adding include=all ensures we find it even if it's soft-deleted
    # Adding fields=connection,owners,tags ensures the dump is complete
    url = f"/services/storageServices/name/{encoded_name}?fields=connection,owners,tags&include=all"
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        # Respect JSON_DIR env var if set, otherwise default to ../json/storageService
        base_json_dir = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
        json_dir = os.path.join(base_json_dir, "storageService")
        os.makedirs(json_dir, exist_ok=True)
        
        file_path = os.path.join(json_dir, f"{service_name}.json")
        
        data = response.json()
        
        # Filter out "patches or mistakes" - per user request
        # We only keep fields that are typically used for creation/import to ensure a clean export
        allowed_fields = ["name", "displayName", "description", "serviceType", "connection", "owners", "tags"]
        export_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        # Sanitize connection config (remove read-only/derived fields like 'supportsX')
        if "connection" in export_data and isinstance(export_data["connection"], dict):
            conn_config = export_data["connection"].get("config", {})
            if isinstance(conn_config, dict):
                keys_to_remove = [k for k in conn_config.keys() if k.startswith("supports")]
                for k in keys_to_remove:
                    del conn_config[k]
                
                # AWS config specific cleanup if it exists
                aws_config = conn_config.get("awsConfig")
                if isinstance(aws_config, dict) and "enabled" in aws_config:
                    del aws_config["enabled"]

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)
            
        print(f"✅ Success! Saved to {file_path}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: Service '{service_name}' not found. (Status: {status})")
        print(text)
        sys.exit(1)

if __name__ == "__main__":
    main()

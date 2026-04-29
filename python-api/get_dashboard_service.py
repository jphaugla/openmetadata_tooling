#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
import subprocess
from om_client import OpenMetadataClient

def load_env_from_sh(file_path):
    """
    Loads environment variables from a shell script by sourcing it in bash.
    This ensures that variable expansions and command substitutions (like $(cat ...))
    are handled correctly.
    """
    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        print(f"⚠️ Warning: Environment file {file_path} not found.")
        return
    
    try:
        # Source the file and then print the environment variables
        command = f"source {path} > /dev/null 2>&1 && env"
        output = subprocess.check_output(["bash", "-c", command], text=True)
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
    except Exception as e:
        print(f"⚠️ Warning: Could not load environment from {file_path}: {e}")

def main():
    # Load environment variables from the specified script
    # The user specifically requested to use ~/.collate/setDemo.sh
    load_env_from_sh("~/.collate/setDemo.sh")

    if len(sys.argv) != 2:
        print("❌ Usage: python get_dashboard_service.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    
    # URL Encoding handles spaces gracefully
    encoded_name = urllib.parse.quote(service_name)
    
    # Now that env is loaded, we can instantiate the client
    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Dashboard Service: {service_name}...")
    
    # We use _make_request directly to get the full JSON payload
    # Fields connection, owners, and tags are typically required for a complete backup/import
    url = f"/services/dashboardServices/name/{encoded_name}?fields=connection,owners,tags&include=all"
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        data = response.json()
        
        # Filter fields to ensure a clean export (consistent with get_storage_service.py)
        allowed_fields = ["name", "displayName", "description", "serviceType", "connection", "owners", "tags"]
        export_data = {k: v for k, v in data.items() if k in allowed_fields}

        # Use the requested directory ~/.collate/json/dashboad
        base_dir = os.environ.get("JSON_DIR", os.path.expanduser("~/.collate/json"))
        json_dir = os.path.join(os.path.expanduser(base_dir), "dashboad")
        os.makedirs(json_dir, exist_ok=True)
        
        file_path = os.path.join(json_dir, f"{service_name}.json")
        
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

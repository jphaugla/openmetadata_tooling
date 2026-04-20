#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_metric.py <metric_name>")
        # Example: python get_metric.py "CLV"
        sys.exit(1)

    metric_name = sys.argv[1]
    
    # URL Encoding handles spaces and special characters in FQNs
    encoded_name = urllib.parse.quote(metric_name)
    
    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Metric: {metric_name}...")
    
    # Endpoint for metrics. Using include=all to find it even if it's not active.
    # Adding fields=owners,tags to match other extraction scripts.
    url = f"/metrics/name/{encoded_name}?fields=owners,tags&include=all"
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        # Determine the base JSON directory. 
        # User requested ~/.collate/json/metric, so we default to ~/.collate/json
        default_json_dir = os.path.expanduser("~/.collate/json")
        json_dir_base = os.environ.get("JSON_DIR", default_json_dir)
        json_dir = os.path.join(json_dir_base, "metric")
        
        os.makedirs(json_dir, exist_ok=True)
        
        # Replace characters that might be invalid in filenames if it's an FQN
        safe_filename = metric_name.replace(".", "_").replace("/", "_")
        file_path = os.path.join(json_dir, f"{safe_filename}.json")
        
        with open(file_path, "w") as f:
            json.dump(response.json(), f, indent=2)
            
        print(f"✅ Success! Saved to {file_path}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: Metric '{metric_name}' not found. (Status: {status})")
        print(f"Response: {text}")
        sys.exit(1)

if __name__ == "__main__":
    main()

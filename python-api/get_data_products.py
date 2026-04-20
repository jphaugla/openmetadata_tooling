#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_data_products.py <data_product_name>")
        # Example: python get_data_products.py "Customer 360"
        sys.exit(1)

    dp_name = sys.argv[1]
    
    # URL Encoding handles spaces and special characters
    encoded_name = urllib.parse.quote(dp_name)
    
    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Data Product: {dp_name}...")
    
    # Endpoint for data products. Including owners, domain, assets, and experts.
    url = f"/dataProducts/name/{encoded_name}?fields=owners,domain,experts,assets&include=all"
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        # Determine the base JSON directory as requested
        default_json_dir = os.path.expanduser("~/.collate/json")
        json_dir_base = os.environ.get("JSON_DIR", default_json_dir)
        json_dir = os.path.join(json_dir_base, "dataProduct")
        
        os.makedirs(json_dir, exist_ok=True)
        
        # Replace characters that might be invalid in filenames
        safe_filename = dp_name.replace(" ", "_").replace(".", "_").replace("/", "_")
        file_path = os.path.join(json_dir, f"{safe_filename}.json")
        
        with open(file_path, "w") as f:
            json.dump(response.json(), f, indent=2)
            
        print(f"✅ Success! Saved to {file_path}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: Data Product '{dp_name}' not found. (Status: {status})")
        print(f"Response: {text}")
        sys.exit(1)

if __name__ == "__main__":
    main()

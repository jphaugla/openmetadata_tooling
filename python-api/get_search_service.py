#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_search_service.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Search Service: {service_name}...")
    
    encoded_name = urllib.parse.quote(service_name)
    url = f"/services/searchServices/name/{encoded_name}?fields=testConnectionResult,owners,tags&include=all"
    
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        data = response.json()
        
        # We need the service ID to ensure we grab everything
        service_id = data.get("id")
        status = data.get("testConnectionResult", {}).get("status", "Unknown (Not Tested)")
        
        print(f"✅ Found {service_name}")
        print(f"🆔 ID: {service_id}")
        print(f"📡 Status: {status}")
        print(f"💾 Exporting JSON definition for ID: {service_id}...")
        
        # Second fetch to mirror original logic (though often the first fetch has everything)
        detail_response = client._make_request("GET", f"/services/searchServices/{service_id}?fields=connection,owners,tags")
        if detail_response and detail_response.status_code == 200:
            json_dir = os.path.join(os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json")), "searchService")
            os.makedirs(json_dir, exist_ok=True)
            
            file_path = os.path.join(json_dir, f"{service_name}.json")
            
            with open(file_path, "w") as f:
                json.dump(detail_response.json(), f, indent=2)
                
            print(f"📂 File saved as: {file_path}")
        else:
            print("❌ Failed to fetch full service details.")
    else:
        status_code = response.status_code if response else "Unknown"
        print(f"❌ Error: Service '{service_name}' not found. (Status: {status_code})")
        sys.exit(1)

if __name__ == "__main__":
    main()

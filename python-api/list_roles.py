#!/usr/bin/env python3
import sys
import json
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    url = "/roles"
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        data = response.json().get("data", [])
        
        # Format the output similar to jq '.data[] | {name: .name, id: .id}'
        formatted = [{"name": r.get("name"), "id": r.get("id")} for r in data]
        
        print(json.dumps(formatted, indent=2))
    else:
        status = response.status_code if response else "Unknown"
        print(f"❌ Error fetching roles. HTTP Status: {status}")
        sys.exit(1)

if __name__ == "__main__":
    main()

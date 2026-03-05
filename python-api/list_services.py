#!/usr/bin/env python3
import json
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    url = "/services/databaseServices?include=all"
    print("🔍 Fetching all defined database services...")
    print(f"🌐 URL: {client.api_base}{url}")
    print("-" * 48)

    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        count = len(data.get("data", []))
        print("-" * 48)
        print(f"✅ Found {count} database services.")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error fetching services. (Status: {status})")
        print(text)

if __name__ == "__main__":
    main()

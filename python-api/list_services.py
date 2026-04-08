#!/usr/bin/env python3
import json
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    url = "/services/databaseServices?include=all&limit=1000"
    print("🔍 Fetching all defined database services...")
    print(f"🌐 URL: {client.api_base}{url}")
    print("-" * 48)

    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        data = response.json()
        services = data.get("data", [])
        
        print(f"{'NAME':<25} | {'TYPE':<15} | {'STATUS':<15} | {'ID'}")
        print("-" * 80)
        
        for s in services:
            name = s.get("name", "N/A")
            svc_type = s.get("serviceType", "N/A")
            deleted = "DELETED" if s.get("deleted") else "Active"
            svc_id = s.get("id", "N/A")
            print(f"{name:<25} | {svc_type:<15} | {deleted:<15} | {svc_id}")
            
        print("-" * 80)
        print(f"✅ Found {len(services)} database services.")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error fetching services. (Status: {status})")
        print(text)

if __name__ == "__main__":
    main()

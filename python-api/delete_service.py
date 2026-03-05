#!/usr/bin/env python3
import sys
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python delete_service.py <SERVICE_NAME>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🗑️  Preparing to HARD DELETE service: {service_name}")
    
    encoded_name = urllib.parse.quote(service_name)
    response = client._make_request("GET", f"/services/databaseServices/name/{encoded_name}")
    
    service_id = None
    if response and response.status_code == 200:
        service_id = response.json().get("id")
    else:
        print(f"❓ {service_name} not found by exact name. Checking fallback list...")
        fallback_res = client._make_request("GET", "/services/databaseServices?limit=100")
        if fallback_res and fallback_res.status_code == 200:
            services = fallback_res.json().get("data", [])
            for s in services:
                if s.get("name") == service_name:
                    service_id = s.get("id")
                    break

    if service_id:
        print(f"✅ Found ID: {service_id}")
        
        # Perform Hard Delete (recursive removes child databases/tables)
        delete_url = f"/services/databaseServices/{service_id}?hardDelete=true&recursive=true"
        delete_res = client._make_request("DELETE", delete_url)
        
        if delete_res and delete_res.status_code == 200:
            print(f"💥 Service {service_name} has been permanently deleted.")
        else:
            err = delete_res.json().get("message", delete_res.text) if delete_res else "Unknown HTTP Error"
            print(f"❌ Failed to delete service: {err}")
    else:
        print("❌ Service not found. Nothing to delete.")
        sys.exit(1)

if __name__ == "__main__":
    main()

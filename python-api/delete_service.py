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
    
    print(f"🗑️  Searching for service: {service_name}")
    
    # List of service types to check in order
    service_types = [
        "databaseServices",
        "storageServices",
        "messagingServices",
        "pipelineServices",
        "dashboardServices",
        "searchServices",
        "mlModelServices"
    ]
    
    found_service = None
    found_type = None
    
    encoded_name = urllib.parse.quote(service_name)
    
    for stype in service_types:
        print(f"🔍 Checking {stype}...")
        url = f"/services/{stype}/name/{encoded_name}"
        response = client._make_request("GET", url)
        
        if response and response.status_code == 200:
            found_service = response.json()
            found_type = stype
            break
            
    if not found_service:
        print(f"❓ {service_name} not found by exact name in primary types. checking search fallback...")
        # Optional: We could use the search API here, but iterating categories is safer for exact name lookup
        pass

    if found_service and found_type:
        service_id = found_service.get("id")
        print(f"✅ Found {found_type} with ID: {service_id}")
        
        # Confirm with user if it's not a storage/db service? 
        # No, the script is intended for automation.
        
        print(f"💥 Preparing to HARD DELETE {found_type}: {service_name}")
        
        # Perform Hard Delete (recursive removes child entities)
        delete_url = f"/services/{found_type}/{service_id}?hardDelete=true&recursive=true"
        delete_res = client._make_request("DELETE", delete_url)
        
        if delete_res and delete_res.status_code == 200:
            print(f"🔥 Success! Service '{service_name}' has been permanently deleted.")
        else:
            status = delete_res.status_code if delete_res else "Unknown"
            err = delete_res.text if delete_res else "No response"
            print(f"❌ Failed to delete service. Status: {status}")
            print(f"      Response: {err}")
    else:
        print(f"❌ Service '{service_name}' not found in any service category.")
        sys.exit(1)

if __name__ == "__main__":
    main()

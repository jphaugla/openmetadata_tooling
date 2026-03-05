#!/usr/bin/env python3
import os
import sys
import time
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    # Configure Sleep Interval & Retries
    sleep_time = int(os.getenv("SLEEP_SECONDS", "10"))
    max_retries = int(os.getenv("MAX_RETRIES", "30"))
    
    status_url = f"{client.api_base}/system/status"
    
    print("🔍 Monitoring Collate Server Status...")
    print(f"🌐 URL: {status_url}")
    print(f"⏸️  Interval: {sleep_time} seconds")
    print("-" * 48)

    # Components that MUST pass for the server to be considered functional
    critical_components = {"database", "searchInstance", "pipelineServiceClient", "jwks"}

    for attempt in range(1, max_retries + 1):
        print(f"📡 Attempt {attempt}/{max_retries}...")
        
        response = client._make_request("GET", "/system/status")
        
        if response and response.status_code == 200:
            data = response.json()
            
            failed_critical = []
            for comp_name, comp_data in data.items():
                if comp_name in critical_components and comp_data.get("passed") is False:
                    failed_critical.append(comp_name)
                    
            if not failed_critical:
                print("✅ Success: Collate server critical components are healthy!")
                
                # Check if migrations are actually failing, and just warn
                migration_status = data.get("migrations", {}).get("passed")
                if migration_status is False:
                    print("⚠️  Note: Migrations are reporting incomplete, but continuing as critical services are up.")
                    
                print(f"📄 Response: {data}")
                sys.exit(0)
            else:
                print(f"⚠️  Critical components failed: {', '.join(failed_critical)}")
        else:
            status = response.status_code if response else "Connection Failed"
            print(f"⚠️  Could not fetch status. HTTP Status: {status}")

        if attempt < max_retries:
            print(f"⏳ Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)

    print(f"❌ Failure: Collate server did not report healthy status after {max_retries} attempts.")
    sys.exit(1)

if __name__ == "__main__":
    main()

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
    
    print("🔍 Monitoring OpenMetadata Server Status...")
    print(f"🌐 URL: {status_url}")
    print(f"⏸️  Interval: {sleep_time} seconds")
    print("-" * 48)

    for attempt in range(1, max_retries + 1):
        print(f"📡 Attempt {attempt}/{max_retries}...")
        
        response = client._make_request("GET", "/system/status")
        
        if response and response.status_code == 200:
            data = response.json()
            
            # The server returns a map of components, each with a "passed" boolean.
            # We consider it healthy if there are no "passed":false entries and at least one "passed":true.
            has_failures = any(comp.get("passed") is False for comp in data.values())
            has_successes = any(comp.get("passed") is True for comp in data.values())
            
            if not has_failures and has_successes:
                print("✅ Success: OpenMetadata server is healthy!")
                print(f"📄 Response: {data}")
                sys.exit(0)
                
            print(f"⚠️  Server not ready or unhealthy. Response: {data}")
        else:
            status = response.status_code if response else "Connection Failed"
            print(f"⚠️  Could not fetch status. HTTP Status: {status}")

        if attempt < max_retries:
            print(f"⏳ Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)

    print(f"❌ Failure: OpenMetadata server did not report healthy status after {max_retries} attempts.")
    sys.exit(1)

if __name__ == "__main__":
    main()

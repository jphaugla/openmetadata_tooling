#!/usr/bin/env python3
import sys
import json
import urllib.parse
from om_client import OpenMetadataClient

def main():
    table_fqn = "Cockroach_movr.movr.public.rides"
    
    if len(sys.argv) > 1:
        table_fqn = sys.argv[1]

    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Lineage for: {table_fqn}...")
    
    encoded_fqn = urllib.parse.quote(table_fqn)
    url = f"/lineage/table/name/{encoded_fqn}?upstreamDepth=1&downstreamDepth=1"
    
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        status = response.status_code if response else "Unknown"
        print(f"❌ Error fetching lineage. HTTP Status: {status}")
        if response:
            print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()

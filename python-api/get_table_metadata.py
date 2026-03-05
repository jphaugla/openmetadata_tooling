#!/usr/bin/env python3
import sys
import json
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Error: No Table FQN provided.")
        print("Usage: python get_table_metadata.py <table_fqn>")
        sys.exit(1)

    table_fqn = sys.argv[1]
    client = OpenMetadataClient()
    
    encoded_fqn = urllib.parse.quote(table_fqn)
    url = f"/tables/name/{encoded_fqn}?fields=tags,extension"
    
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        status = response.status_code if response else "Unknown"
        print(f"❌ Error fetching table metadata. HTTP Status: {status}")
        if response:
            print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys
import json
import os
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    print("🔍 Fetching Ingestion IP...")
    
    # Endpoint for fetching the ingestion IP
    url = "/services/ingestionPipelines/ip"
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        data = response.json()
        ingestion_ip = data.get("ip")
        
        print("\n" + "="*50)
        print(f"✅ Ingestion IP: {ingestion_ip}")
        print("="*50)
        
        print("\nℹ️  Explanation of IPs used in OpenMetadata / Collate:")
        print("-" * 50)
        print(f"1. Ingestion IP ({ingestion_ip}):")
        print("   This is the IP address of the ingestion agent (e.g., Airflow).")
        print("   You MUST whitelist this IP in your database or data warehouse firewall")
        print("   to allow OpenMetadata to pull metadata and run profiling.")
        
        print("\n2. Application IP:")
        print("   This is the IP address where the OpenMetadata UI/API is hosted.")
        print("   Users connect to this IP to browse the catalog.")
        
        print("\n3. Egress IPs:")
        print("   In some cloud environments, the outgoing traffic (egress) might come from")
        print("   a range of IPs or a NAT gateway. If whitelisting the single Ingestion IP")
        print("   doesn't work, you may need to whitelist the entire CIDR range for the region.")
        print("-" * 50)
        
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: Could not fetch Ingestion IP. (Status: {status})")
        print(text)
        sys.exit(1)

if __name__ == "__main__":
    main()

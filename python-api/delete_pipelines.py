#!/usr/bin/env python3
import sys
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python delete_pipelines.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Finding pipelines to delete for service: {service_name}...")
    
    pipelines = client.get_pipelines_for_service(service_name)
    
    if not pipelines:
        print(f"✅ No pipelines found for {service_name}. Nothing to delete.")
        sys.exit(0)
        
    for p in pipelines:
        p_id = p.get("id")
        p_name = p.get("name")
        
        print(f"🗑️  Deleting Pipeline: {p_name} ({p_id})...")
        
        if client.delete_pipeline(p_id):
            print("   ✅ Deleted.")
        else:
            print("   ❌ Failed to delete.")

    print("-" * 42)
    print(f"🧹 Cleanup complete for {service_name}")

if __name__ == "__main__":
    main()

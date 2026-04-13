#!/usr/bin/env python3
import sys
import urllib.parse
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    # FQNs
    users_fqn = "Cockroach_movr.movr.public.users"
    rides_fqn = "Cockroach_movr.movr.public.rides"
    view_fqn = "Cockroach_movr.movr.public.customer_summary_view"
    
    print("🔍 Fetching Entity IDs...")
    
    def get_table_id(fqn):
        encoded = urllib.parse.quote(fqn)
        response = client._make_request("GET", f"/tables/name/{encoded}")
        return response.json().get("id") if response and response.status_code == 200 else None
        
    users_id = get_table_id(users_fqn)
    rides_id = get_table_id(rides_fqn)
    view_id = get_table_id(view_fqn)
    
    if not users_id or not rides_id or not view_id:
        print("❌ Error: Could not find one or more entities.")
        print(f"Users ID: {users_id}")
        print(f"Rides ID: {rides_id}")
        print(f"View ID: {view_id}")
        sys.exit(1)
        
    print("✅ Found IDs:")
    print(f"   Users: {users_id}")
    print(f"   Rides: {rides_id}")
    print(f"   View:  {view_id}")
    
    # helper for adding lineage edges
    def add_lineage(from_id, to_id):
        payload = {
            "edge": {
                "fromEntity": {"id": from_id, "type": "table"},
                "toEntity": {"id": to_id, "type": "table"}
            }
        }
        res = client._make_request("PUT", "/lineage", json=payload)
        if res and res.status_code == 200:
            print("   ✅ Success")
        else:
            err = res.json().get("message", res.text) if res else "Unknown HTTP Error"
            print(f"   ❌ Failed: {err}")
            
    # 2. Link Users -> View
    print("\n🔗 Linking Users to View...")
    add_lineage(users_id, view_id)
    
    # 3. Link Rides -> View
    print("\n🔗 Linking Rides to View...")
    add_lineage(rides_id, view_id)
    
    print("\n✅ Lineage creation complete!")

if __name__ == "__main__":
    main()

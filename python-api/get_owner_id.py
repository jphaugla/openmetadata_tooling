#!/usr/bin/env python3
import sys
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Error: No Owner Name provided.")
        print("Usage: python get_owner_id.py <owner_name>")
        sys.exit(1)

    owner_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Searching for User: {owner_name}...")
    
    encoded_name = urllib.parse.quote(owner_name)
    response = client._make_request("GET", f"/users/name/{encoded_name}")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"✅ Found User: {owner_name}")
        print(f"🆔 ID: {data.get('id')}")
        print(f"👑 Admin: {data.get('isAdmin', False)}")
        print(f"🤖 Bot: {data.get('isBot', False)}")
    else:
        print(f"❓ {owner_name} not found via direct name lookup. Checking fallback search...")
        
        # Fallback: Search the users list (useful if name case-sensitivity is an issue)
        fallback_response = client._make_request("GET", "/users?limit=100")
        
        if fallback_response and fallback_response.status_code == 200:
            users = fallback_response.json().get("data", [])
            
            # Case-insensitive search
            found_user = next((u for u in users if u.get("name", "").lower() == owner_name.lower()), None)
            
            if found_user:
                print(f"⚠️ Found via fallback! ID: {found_user.get('id')}")
                print(f"   Note: Exact name in system is '{found_user.get('name')}'")
            else:
                print(f"❌ User '{owner_name}' could not be found. Check if the name matches exactly in the UI.")
        else:
            print("❌ Fallback search failed.")

if __name__ == "__main__":
    main()

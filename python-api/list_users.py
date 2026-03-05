#!/usr/bin/env python3
import sys
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    url = "/users?limit=100"
    print("🔍 Fetching users list...")
    print("-" * 48)

    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        data = response.json().get("data", [])
        
        for user in data:
            name = user.get("name")
            display = user.get("displayName", "N/A")
            uid = user.get("id")
            is_admin = user.get("isAdmin", False)
            is_bot = user.get("isBot", False)
            
            print(f"Name: {name}")
            print(f"Display: {display}")
            print(f"ID: {uid}")
            print(f"Admin: {is_admin}")
            print(f"Bot: {is_bot}")
            print("---")
            
    elif response and response.status_code == 401:
         print("❌ Error: 401 Unauthorized. Your TOKEN is likely expired or invalid.")
         print("💡 Try logging into the UI and generating a new token.")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: API request failed with HTTP {status}")
        print(text)

if __name__ == "__main__":
    main()

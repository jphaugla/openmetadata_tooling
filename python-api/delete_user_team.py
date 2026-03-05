#!/usr/bin/env python3
import sys
import urllib.parse
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    user_name = "jason.haugland"
    team_name = "Solution Architects"
    
    # 1. Get User ID
    encoded_user = urllib.parse.quote(user_name)
    user_resp = client._make_request("GET", f"/users/name/{encoded_user}")
    user_id = user_resp.json().get("id") if user_resp and user_resp.status_code == 200 else None
    
    # 2. Get Team ID
    encoded_team = urllib.parse.quote(team_name)
    team_resp = client._make_request("GET", f"/teams/name/{encoded_team}")
    team_id = team_resp.json().get("id") if team_resp and team_resp.status_code == 200 else None
    
    # 3. Hard Delete User
    print(f"🗑 Deleting User: {user_name}...")
    if user_id:
        del_user = client._make_request("DELETE", f"/users/{user_id}?hardDelete=true&recursive=true")
        if del_user and del_user.status_code == 200:
            print("   ✅ User deleted.")
        else:
            print("   ❌ Failed to delete user.")
    else:
        print(f"   ⚠️ User '{user_name}' not found.")
        
    # 4. Hard Delete Team
    print(f"🗑 Deleting Team: {team_name}...")
    if team_id:
        del_team = client._make_request("DELETE", f"/teams/{team_id}?hardDelete=true&recursive=true")
        if del_team and del_team.status_code == 200:
            print("   ✅ Team deleted.")
        else:
            print("   ❌ Failed to delete team.")
    else:
        print(f"   ⚠️ Team '{team_name}' not found.")
        
    print("\n✅ Ghost entities purged.")

if __name__ == "__main__":
    main()

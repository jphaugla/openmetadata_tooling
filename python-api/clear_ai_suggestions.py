#!/usr/bin/env python3
import requests
import os
import sys
import json

BASE_URL = os.environ.get("API_BASE")
if not BASE_URL:
    print("❌ API_BASE environment variable not set. Run: source ~/.collate/setJson.sh")
    sys.exit(1)
BOT_NAME = "collateaiapplicationbot"

def get_headers():
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN environment variable not set. Run: source ~/.collate/setJson.sh")
        sys.exit(1)
    return {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

def main():
    headers = get_headers()
    
    # 1. Find the Bot User ID
    print(f"🔍 Finding Bot User: {BOT_NAME}...")
    bot_res = requests.get(f"{BASE_URL}/users/name/{BOT_NAME}", headers=headers)
    if bot_res.status_code != 200:
        print(f"❌ Could not find bot user '{BOT_NAME}'. Status: {bot_res.status_code}")
        return
    
    bot_id = bot_res.json().get("id")
    print(f"✅ Found Bot ID: {bot_id}")

    # 2. List all suggestions created by this bot
    # We'll use a search or list on the suggestions endpoint if supported,
    # but usually we list them per entity or use the global suggestions endpoint.
    print("Searching for AI suggestions to clear...")
    
    # In newer Collate versions, suggestions are accessible via /suggestions
    # We'll filter by the bot's ID
    sugg_res = requests.get(f"{BASE_URL}/suggestions?createdBy={bot_id}&limit=1000", headers=headers)
    
    if sugg_res.status_code != 200:
        print(f"❌ Failed to fetch suggestions. Status: {sugg_res.status_code}")
        return

    suggestions = sugg_res.json().get("data", [])
    if not suggestions:
        print("ℹ️  No active AI suggestions found to clear.")
        return

    print(f"🗑️  Found {len(suggestions)} suggestions. Deleting...")
    
    deleted_count = 0
    for sugg in suggestions:
        s_id = sugg.get("id")
        del_res = requests.delete(f"{BASE_URL}/suggestions/{s_id}", headers=headers)
        if del_res.status_code in [200, 204]:
            deleted_count += 1
        else:
            print(f"⚠️  Failed to delete suggestion {s_id}: {del_res.status_code}")

    print(f"✅ Successfully cleared {deleted_count} AI suggestions.")
    print("🚀 You can now rerun your AI Description Agent to populate the descriptions fresh.")

if __name__ == "__main__":
    main()

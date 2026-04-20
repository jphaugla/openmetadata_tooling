#!/usr/bin/env python3
"""
Script to import a Persona definition into OpenMetadata/Collate.
Sourcing ~/.collate/setJsonh.sh if environment variables are not set.
"""
import sys
import json
import os
import subprocess
from om_client import OpenMetadataClient

def load_collate_env():
    """
    Checks for TOKEN and API_BASE. If missing, attempts to source ~/.collate/setJsonh.sh.
    """
    if os.getenv("TOKEN") and os.getenv("API_BASE"):
        return

    # User explicitly asked for setJsonh.sh
    env_file = os.path.expanduser("~/.collate/setJsonh.sh")
    if not os.path.exists(env_file):
        # Fallback to setJson.sh if setJsonh.sh is missing (common typo or variation)
        alt_env_file = os.path.expanduser("~/.collate/setJson.sh")
        if os.path.exists(alt_env_file):
            print(f"ℹ️ {env_file} not found, using {alt_env_file} instead.")
            env_file = alt_env_file
        else:
            print(f"⚠️ Warning: TOKEN/API_BASE not set and {env_file} not found.")
            return

    print(f"ℹ️ Sourcing environment from {env_file}...")
    # Running a shell to source the file and capture the environment
    command = f"source {env_file} && env"
    try:
        # We use zsh as it's the default on Mac
        result = subprocess.run(['/bin/zsh', '-c', command], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                # Only set keys we might care about if they aren't already set
                if key in ["TOKEN", "API_BASE", "OWNER_ID", "JSON_DIR"]:
                    os.environ[key] = value
    except Exception as e:
        print(f"❌ Error sourcing {env_file}: {e}")

def main():
    load_collate_env()

    if len(sys.argv) != 2:
        print("❌ Usage: python import_persona.py <persona_json_file>")
        print("Example: python import_persona.py ~/.collate/json/persona/Business_User.json")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r") as f:
        try:
            persona_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in file '{input_file}'.\n{e}")
            sys.exit(1)

    client = OpenMetadataClient()
    
    # Prepping Create/Update Persona Payload
    persona_name = persona_data.get("name")
    print(f"🚀 Importing Persona: {persona_name}")

    # OpenMetadata Persona Create/Update schema
    create_payload = {
        "name": persona_name,
        "displayName": persona_data.get("displayName"),
        "description": persona_data.get("description"),
    }
    
    # Map users from objects to IDs if they exist
    if "users" in persona_data:
        target_user_ids = []
        print("👤 Resolving users on target system...")
        for user in persona_data["users"]:
            if isinstance(user, dict) and "name" in user:
                uname = user["name"]
                import urllib.parse
                enc_name = urllib.parse.quote(uname)
                res = client._make_request("GET", f"/users/name/{enc_name}")
                if res and res.status_code == 200:
                    target_user_ids.append(res.json().get("id"))
                    print(f"   ✅ User '{uname}' resolved.")
                else:
                    print(f"   ⚠️ User '{uname}' not found on target system. Skipping.")
            elif isinstance(user, str):
                target_user_ids.append(user)
        create_payload["users"] = target_user_ids

    # Map roles if they exist
    if "roles" in persona_data:
        target_role_ids = []
        print("🔐 Resolving roles on target system...")
        for role in persona_data["roles"]:
            if isinstance(role, dict) and "name" in role:
                rname = role["name"]
                import urllib.parse
                enc_name = urllib.parse.quote(rname)
                res = client._make_request("GET", f"/roles/name/{enc_name}")
                if res and res.status_code == 200:
                    target_role_ids.append(res.json().get("id"))
                    print(f"   ✅ Role '{rname}' resolved.")
                else:
                    print(f"   ⚠️ Role '{rname}' not found on target system. Skipping.")
            elif isinstance(role, str):
                target_role_ids.append(role)
        create_payload["roles"] = target_role_ids

    # Using PUT /personas for idempotency (create or update)
    # Most OpenMetadata entities support this pattern
    print(f"📡 Sending PUT request for Persona '{persona_name}'...")
    response = client._make_request("PUT", "/personas", json=create_payload)
    
    if response is not None and response.status_code in [200, 201]:
        action = "Created" if response.status_code == 201 else "Updated"
        print(f"✅ Success! {action} Persona '{persona_name}' (ID: {response.json().get('id')})")
    else:
        status = response.status_code if response is not None else "Unknown"
        text = response.text if response is not None else ""
        print(f"❌ Error: Failed to import persona '{persona_name}'. (Status: {status})")
        if text:
            print(text)
        sys.exit(1)

if __name__ == "__main__":
    main()

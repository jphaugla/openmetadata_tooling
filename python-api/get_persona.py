#!/usr/bin/env python3
"""
Script to fetch a Persona definition from OpenMetadata/Collate.
Sourcing ~/.collate/setDemo.sh if environment variables are not set.
"""
import sys
import json
import os
import urllib.parse
import subprocess
from om_client import OpenMetadataClient

def load_collate_env():
    """
    Checks for TOKEN and API_BASE. If missing, attempts to source ~/.collate/setDemo.sh.
    """
    if os.getenv("TOKEN") and os.getenv("API_BASE"):
        return

    env_file = os.path.expanduser("~/.collate/setDemo.sh")
    if not os.path.exists(env_file):
        print(f"⚠️ Warning: TOKEN/API_BASE not set and {env_file} not found.")
        return

    print(f"ℹ️ Sourcing environment from {env_file}...")
    # Running a shell to source the file and capture the environment
    command = f"source {env_file} && env"
    try:
        # We use zsh as it's the default on Mac and likely what the user uses
        result = subprocess.run(['/bin/zsh', '-c', command], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                # Only set keys we might care about if they aren't already set
                if key in ["TOKEN", "API_BASE", "JSON_DIR"]:
                    os.environ[key] = value
    except Exception as e:
        print(f"❌ Error sourcing {env_file}: {e}")

def main():
    load_collate_env()

    if len(sys.argv) != 2:
        print("❌ Usage: python get_persona.py <persona_name>")
        print("Example: python get_persona.py \"Business User\"")
        sys.exit(1)

    persona_name = sys.argv[1]
    encoded_name = urllib.parse.quote(persona_name)
    
    client = OpenMetadataClient()
    
    print(f"🔍 Fetching Persona: {persona_name}...")
    
    # Adding fields=users to get the full definition including assigned users
    url = f"/personas/name/{encoded_name}?fields=users"
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        persona_data = response.json()
        
        # Consistent with other scripts: Use JSON_DIR or ../json/persona
        default_json_dir = os.path.join(os.path.dirname(__file__), "..", "json")
        base_json_dir = os.environ.get("JSON_DIR", default_json_dir)
        # Expand ~ if present in JSON_DIR
        base_json_dir = os.path.expanduser(base_json_dir)
        
        persona_dir = os.path.join(base_json_dir, "persona")
        os.makedirs(persona_dir, exist_ok=True)
        
        # Clean name for filename (e.g. "Business User" -> "Business_User")
        safe_name = persona_name.replace(" ", "_").replace("/", "_")
        file_path = os.path.join(persona_dir, f"{safe_name}.json")
        
        with open(file_path, "w") as f:
            json.dump(persona_data, f, indent=2)
            
        print(f"✅ Success! Saved to {file_path}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else ""
        print(f"❌ Error: Persona '{persona_name}' not found. (Status: {status})")
        if text:
            print(text)
        sys.exit(1)

if __name__ == "__main__":
    main()

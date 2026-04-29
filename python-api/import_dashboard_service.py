#!/usr/bin/env python3
import sys
import json
import os
import subprocess
from om_client import OpenMetadataClient

def load_env_from_sh(file_path):
    """
    Loads environment variables from a shell script by sourcing it in bash.
    This ensures that variable expansions and command substitutions are handled correctly.
    """
    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        print(f"⚠️ Warning: Environment file {file_path} not found.")
        return
    
    try:
        # Source the file and then print the environment variables
        command = f"source {path} > /dev/null 2>&1 && env"
        output = subprocess.check_output(["bash", "-c", command], text=True)
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
    except Exception as e:
        print(f"⚠️ Warning: Could not load environment from {file_path}: {e}")

def main():
    # Load environment variables from the specified script
    # The user specifically requested to use ~/.collate/setJson.sh
    load_env_from_sh("~/.collate/setJson.sh")

    if len(sys.argv) != 2:
        print("❌ Usage: python import_dashboard_service.py <service_json_file_path>")
        print("Example: python import_dashboard_service.py ~/.collate/json/dashboad/PowerBIPROD.json")
        sys.exit(1)

    input_file = os.path.expanduser(sys.argv[1])
    
    if not os.path.isfile(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r") as f:
        try:
            service_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in file '{input_file}'.\n{e}")
            sys.exit(1)

    # Now that env is loaded, we can instantiate the client
    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID in setJson.sh.")
        sys.exit(1)

    # 1. Resolve Owner Name (to ensure the owner exists on the target system)
    print(f"👤 Resolving name for Owner ID: {owner_id}...")
    user_data = client.get_user_by_id(owner_id)
    if not user_data or "name" not in user_data:
        print(f"❌ Error: Could not find user name for ID {owner_id} on target system.")
        print("Please check if the OWNER_ID is correct for the target environment.")
        sys.exit(1)
        
    owner_name = user_data["name"]
    print(f"✅ Owner resolved: {owner_name}")

    # 2. Build Create Payload
    name = service_data.get("name")
    service_type = service_data.get("serviceType")
    print(f"🔗 Prepping Import for Dashboard Service ({service_type}): {name}")

    create_payload = {
        "name": name,
        "serviceType": service_type,
        "connection": service_data.get("connection"),
        "owners": [{"id": owner_id, "type": "user"}]
    }

    # Add optional fields if they exist
    if "displayName" in service_data:
        create_payload["displayName"] = service_data["displayName"]
    if "description" in service_data:
        create_payload["description"] = service_data["description"]

    # Sanitize connection config (remove internal OpenMetadata fields like supportsX)
    conn_config = create_payload.get("connection", {}).get("config", {})
    if isinstance(conn_config, dict):
        # 1. Remove "supportsX" fields which are read-only/derived
        keys_to_remove = [k for k in conn_config.keys() if k.startswith("supports")]
        for k in keys_to_remove:
            del conn_config[k]

        # 2. Strip any leftover "secret:/" pointers that cannot be automatically resolved
        for key in list(conn_config.keys()):
            val = conn_config[key]
            if isinstance(val, str) and val.startswith("secret:/"):
               del conn_config[key]

        # 3. Inject real secrets from local vault
        secret_file = os.path.expanduser(f"~/.collate/secrets/{name}.json")
        if os.path.isfile(secret_file):
            print(f"   🔐 Found local secrets vault for '{name}', safely injecting key material...")
            with open(secret_file, "r") as sf:
                try:
                    local_secrets = json.load(sf)
                    for k, v in local_secrets.items():
                        conn_config[k] = v
                except json.JSONDecodeError:
                    print(f"   ⚠️ Warning: Invalid JSON in secrets file {secret_file}")

    print("----------------------------------------------------------------")
    print(f"🚀 Importing Dashboard Service: {name} to {os.getenv('API_BASE')}")

    # 3. Create Service
    response = client._make_request("POST", "/services/dashboardServices", json=create_payload)
    
    if response is not None and response.status_code in [200, 201]:
        print(f"   ✅ Created (ID: {response.json().get('id')})")
    else:
        status = response.status_code if response is not None else "Unknown"
        text = response.text if response is not None and response.text else "No error message provided by server"
        print(f"   ❌ Failed to create service. Status: {status}")
        print(f"      Response: {text}")

if __name__ == "__main__":
    main()

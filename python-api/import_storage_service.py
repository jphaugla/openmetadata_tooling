#!/usr/bin/env python3
import sys
import json
import os
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python import_storage_service.py <service_json_file_path_or_name> [region]")
        print("Example: python import_storage_service.py $JSON_DIR/storageService/S3-Interchange.json")
        print("Example (Legacy): python import_storage_service.py S3-Interchange us-east-2")
        sys.exit(1)

    input_arg = sys.argv[1]
    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    # Resolve owner to be safe
    print(f"👤 Resolving owner for ID: {owner_id}...")
    user_data = client.get_user_by_id(owner_id)
    if not user_data or "name" not in user_data:
        print(f"❌ Error: Could not find user name for ID {owner_id}.")
        sys.exit(1)

    # Check if input is a file or a service name that exists in JSON_DIR
    json_dir = os.environ.get("JSON_DIR")
    potential_json_path = os.path.join(json_dir, "storageService", f"{input_arg}.json") if json_dir else None
    
    if os.path.isfile(input_arg):
        target_json = input_arg
    elif potential_json_path and os.path.isfile(potential_json_path):
        target_json = potential_json_path
    else:
        target_json = None

    if target_json:
        print(f"📄 Loading service data from file: {target_json}")
        with open(target_json, "r") as f:
            try:
                service_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ Error: Invalid JSON in file '{target_json}'.\n{e}")
                sys.exit(1)
    else:
        # Legacy/Simple mode
        service_name = input_arg
        # Note: Defaulting to us-east-2 if no file is found and no region provided
        region = sys.argv[2] if len(sys.argv) > 2 else "us-east-2" 
        print(f"⚠️  No JSON export found for '{service_name}'. Falling back to simple payload.")
        print(f"🛠 Creating basic S3 service payload for {service_name} in {region}...")
        service_data = {
            "name": service_name,
            "serviceType": "S3",
            "connection": {
                "config": {
                    "type": "S3",
                    "awsConfig": {
                        "awsRegion": region
                    }
                }
            }
        }

    # Prepare Create Payload (Ensure owners is set correctly to current environment's owner)
    create_payload = {
        "name": service_data.get("name"),
        "serviceType": service_data.get("serviceType", "S3"),
        "connection": service_data.get("connection"),
        "owners": [{"id": owner_id, "type": "user"}]
    }
    
    if "displayName" in service_data:
        create_payload["displayName"] = service_data["displayName"]
    if "description" in service_data:
        create_payload["description"] = service_data["description"]

    # Final cleanup of connection config just in case (same logic as export but as a safety)
    if create_payload.get("connection") and isinstance(create_payload["connection"], dict):
        conn_config = create_payload["connection"].get("config", {})
        if isinstance(conn_config, dict):
            keys_to_remove = [k for k in conn_config.keys() if k.startswith("supports")]
            for k in keys_to_remove:
                del conn_config[k]
            
            aws_config = conn_config.get("awsConfig")
            if isinstance(aws_config, dict) and "enabled" in aws_config:
                del aws_config["enabled"]

    print(f"🚀 Importing Storage Service: {create_payload['name']}...")
    response = client._make_request("POST", "/services/storageServices", json=create_payload)
    
    if response and response.status_code in [200, 201]:
        print(f"✅ Success! Created/Updated service ID: {response.json().get('id')}")
    else:
        status = response.status_code if response else "Unknown"
        text = response.text if response else "No response"
        print(f"❌ Failed to create service. Status: {status}")
        print(f"      Response: {text}")

if __name__ == "__main__":
    main()

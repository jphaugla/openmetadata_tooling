#!/usr/bin/env python3
import sys
import json
import os
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python import_db_service.py <service_json_file_path>")
        print("Example: python import_db_service.py $JSON_DIR/Cockroach_tpcc.json")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not os.path.isfile(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r") as f:
        try:
            service_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in file '{input_file}'.\n{e}")
            sys.exit(1)

    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    # 1. Resolve Owner Name
    print(f"👤 Resolving name for Owner ID: {owner_id}...")
    user_data = client.get_user_by_id(owner_id)
    if not user_data or "name" not in user_data:
        print(f"❌ Error: Could not find user name for ID {owner_id}.")
        sys.exit(1)
        
    owner_name = user_data["name"]

    # 2. Build Create Payload
    name = service_data.get("name")
    service_type = service_data.get("serviceType")
    print(f"🔗 Prepping Import for {service_type}: {name}")

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

    # Inject CockroachDB specific workaround (from previous fix)
    if service_type == "Cockroach":
        conn_config = create_payload.get("connection", {}).get("config", {})
        conn_config["options"] = "-c allow_unsafe_internals=true"
        # Optional: remove the old invalid flag if it happens to be in the JSON
        conn_config.pop("connectionOptions", None)

    print("----------------------------------------------------------------")
    print(f"🚀 Importing Service: {name}")

    # 3. Create Service
    response = client._make_request("POST", "/services/databaseServices", json=create_payload)
    
    if response is not None and response.status_code in [200, 201]:
        print(f"   ✅ Created (ID: {response.json().get('id')})")
    else:
        status = response.status_code if response is not None else "Unknown"
        text = response.text if response is not None and response.text else "No error message provided by server"
        print(f"   ❌ Failed to create service. Status: {status}")
        print(f"      Response: {text}")

if __name__ == "__main__":
    main()

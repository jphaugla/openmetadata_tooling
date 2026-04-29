#!/usr/bin/env python3
import sys
import json
import os
import subprocess
from om_client import OpenMetadataClient

def load_env_from_sh(file_path):
    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        return
    try:
        command = f"source {path} > /dev/null 2>&1 && env"
        output = subprocess.check_output(["bash", "-c", command], text=True)
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
    except Exception as e:
        print(f"⚠️ Warning: Could not load environment from {file_path}: {e}")

def import_asset(client, endpoint, file_path, target_service, owner_id):
    with open(file_path, "r") as f:
        data = json.load(f)

    name = data.get("name")
    print(f"🚀 Prepping import for: {name} ({endpoint})")

    # Build Create Payload
    create_payload = {
        "name": name,
        "displayName": data.get("displayName"),
        "description": data.get("description"),
        "service": target_service, # Map to the target service name (e.g. PowerBIPROD_v2)
        "owners": [{"id": owner_id, "type": "user"}] if owner_id else None,
        "tags": data.get("tags")
    }

    # Entity specific fields
    if "datamodels" in endpoint:
        create_payload["columns"] = data.get("columns")
        create_payload["dataModelType"] = data.get("dataModelType")
        create_payload["sql"] = data.get("sql")
    else:
        # Dashboards
        create_payload["sourceUrl"] = data.get("dashboardUrl") # Map dashboardUrl to sourceUrl for creation
        create_payload["dashboardType"] = data.get("dashboardType", "Dashboard")
        
        # Restore charts support using FQNs
        charts = data.get("charts", [])
        if charts:
            create_payload["charts"] = [c.get("fullyQualifiedName") for c in charts if c.get("fullyQualifiedName")]

    # Post to target with a generous timeout to handle complex server-side validation
    try:
        response = client._make_request("POST", endpoint, json=create_payload, timeout=120)
    except Exception as e:
        print(f"   🔥 Exception during request: {e}")
        return False
    if response and response.status_code in [200, 201]:
        print(f"   ✅ Success: {name} (ID: {response.json().get('id')})")
        return True
    else:
        status = response.status_code if response else "Unknown"
        error_text = response.text if response else "No response"
        print(f"   ❌ Failed: {name} (Status: {status})")
        print(f"      Error: {error_text}")
        return False

def main():
    load_env_from_sh("~/.collate/setJson.sh")
    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    # Target service name - we adjusted this to v2 earlier to avoid AWS secret issues
    target_service = "PowerBIPROD_v2"
    
    base_dir = os.environ.get("JSON_DIR", os.path.expanduser("~/.collate/json"))
    
    # 1. Import Data Models
    model_dir = os.path.join(os.path.expanduser(base_dir), "dashboardDataModel")
    if os.path.exists(model_dir):
        print("\n📂 Importing Dashboard Data Models...")
        for f in os.listdir(model_dir):
            if f.endswith(".json"):
                import_asset(client, "/dashboard/datamodels", os.path.join(model_dir, f), target_service, owner_id)

    # 2. Import Dashboards
    dashboard_dir = os.path.join(os.path.expanduser(base_dir), "dashboard")
    if os.path.exists(dashboard_dir):
        print("\n📂 Importing Dashboards...")
        for f in os.listdir(dashboard_dir):
            if f.endswith(".json"):
                import_asset(client, "/dashboards", os.path.join(dashboard_dir, f), target_service, owner_id)

if __name__ == "__main__":
    main()

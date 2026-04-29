#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
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

def export_assets(client, service_name, entity_type, names_to_export):
    """
    Exports entities of a specific type for a given service.
    entity_type can be 'dashboards' or 'dashboard/datamodels'
    """
    print(f"🔍 Searching for {entity_type} in service '{service_name}'...")
    
    # We use a large limit to find all candidates
    fields = "owners,tags"
    if "datamodels" in entity_type:
        fields += ",columns" # Data models have columns
    else:
        fields += ",charts"  # Dashboards have charts
        
    url = f"/{entity_type}?service={urllib.parse.quote(service_name)}&limit=1000&fields={fields}"
        
    response = client._make_request("GET", url)
    if not response or response.status_code != 200:
        print(f"❌ Error fetching {entity_type}")
        return

    data = response.json().get("data", [])
    
    # Map to subfolder names
    folder_map = {
        "dashboards": "dashboard",
        "dashboard/datamodels": "dashboardDataModel"
    }
    subfolder = folder_map.get(entity_type, "misc")
    
    base_dir = os.environ.get("JSON_DIR", os.path.expanduser("~/.collate/json"))
    export_dir = os.path.join(os.path.expanduser(base_dir), subfolder)
    os.makedirs(export_dir, exist_ok=True)

    found_count = 0
    for entity in data:
        display_name = entity.get("displayName")
        name = entity.get("name")
        
        # Check if the name or display name matches our target list
        if any(target.lower() in [name.lower(), (display_name or "").lower()] for target in names_to_export):
            # Fetch full definition for this specific entity to be sure
            entity_id = entity.get("id")
            detail_url = f"/{entity_type}/{entity_id}?fields={fields}"
                
            detail_res = client._make_request("GET", detail_url)
            if detail_res and detail_res.status_code == 200:
                full_entity = detail_res.json()
                # Use display name for filename if available, otherwise name
                filename = (display_name or name).replace("/", "_") + ".json"
                file_path = os.path.join(export_dir, filename)
                
                with open(file_path, "w") as f:
                    json.dump(full_entity, f, indent=2)
                
                print(f"✅ Exported: {filename}")
                found_count += 1

    print(f"🏁 Finished {entity_type}. Total entities exported: {found_count}")

def main():
    load_env_from_sh("~/.collate/setDemo.sh")
    client = OpenMetadataClient()

    service_name = "PowerBIPROD"
    
    # Dashboards requested: Customer, Customer Profitability Sample, Supplier Quality Analysis Sample
    dashboards = ["Customer", "Customer Profitability Sample", "Supplier Quality Analysis Sample"]
    
    # Models requested: Customer Profitability Sample
    models = ["Customer Profitability Sample"]

    print(f"🚀 Starting export for service: {service_name}")
    
    # 1. Export Dashboards
    export_assets(client, service_name, "dashboards", dashboards)
    
    # 2. Export Data Models
    export_assets(client, service_name, "dashboard/datamodels", models)

if __name__ == "__main__":
    main()

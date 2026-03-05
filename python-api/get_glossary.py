#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_glossary.py <glossary_name>")
        sys.exit(1)

    glossary_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Checking for Glossary: {glossary_name}...")
    
    encoded_name = urllib.parse.quote(glossary_name)
    url = f"/glossaries/name/{encoded_name}?fields=owners,tags"
    
    response = client._make_request("GET", url)
    
    if response and response.status_code == 200:
        glossary_data = response.json()
        glossary_id = glossary_data.get("id")
        
        print(f"✅ Found Glossary: {glossary_name} (ID: {glossary_id})")
        print("📦 Fetching Glossary Terms...")
        
        terms_url = f"/glossaryTerms?glossary={glossary_id}&limit=1000"
        terms_response = client._make_request("GET", terms_url)
        
        terms_data = []
        if terms_response and terms_response.status_code == 200:
            terms_data = terms_response.json().get("data", [])
            
        combined_data = {
            "glossary": glossary_data,
            "terms": terms_data
        }
        
        # Format filename correctly spaces -> underscores
        safe_name = glossary_name.replace(" ", "_")
        file_name = f"{safe_name}_glossary.json"
        
        json_dir = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
        os.makedirs(json_dir, exist_ok=True)
        file_path = os.path.join(json_dir, file_name)
        
        print(f"💾 Saving to {file_path}...")
        
        with open(file_path, "w") as f:
            json.dump(combined_data, f, indent=2)
            
        print(f"✨ Done! Exported to {file_name}")
    else:
        print(f"❌ Glossary '{glossary_name}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()

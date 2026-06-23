#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python import_glossary.py <exported_glossary.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not os.path.isfile(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in file '{input_file}'.\n{e}")
            sys.exit(1)

    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    source_glossary = data.get("glossary", {})
    source_terms = data.get("terms", [])
    
    if not source_glossary:
        print(f"❌ Error: 'glossary' object not found in JSON.")
        sys.exit(1)

    print(f"🚀 Importing Glossary from: {input_file}")
    print(f"👤 Assigning Owner ID: {owner_id}")

    # 1. Import Glossary
    glossary_payload = {
        "name": source_glossary.get("name"),
        "displayName": source_glossary.get("displayName"),
        "description": source_glossary.get("description"),
        "mutuallyExclusive": source_glossary.get("mutuallyExclusive", False),
        "owners": [{"id": owner_id, "type": "user"}]
    }

    print("📡 Sending POST request for Glossary...")
    # 1. Import Glossary
    response = client._make_request("POST", "/glossaries", json=glossary_payload)
    
    new_glossary_name = glossary_payload["name"]
    new_glossary_id = None

    if response is not None and response.status_code in [200, 201]:
        new_glossary_id = response.json().get("id")
    elif response is not None and response.status_code == 409:
        print("ℹ️ Glossary already exists. Fetching existing definition...")
        encoded_gname = urllib.parse.quote(new_glossary_name)
        get_response = client._make_request("GET", f"/glossaries/name/{encoded_gname}")
        if get_response is not None and get_response.status_code == 200:
            new_glossary_id = get_response.json().get("id")
            
    if not new_glossary_id:
        print("❌ Failed to import or resolve glossary.")
        status = response.status_code if response is not None else "Unknown"
        text = response.text if response is not None else "No response"
        print(f"💬 Server Status: {status}")
        print(f"💬 Server Response: {text}")
        sys.exit(1)

    print(f"✅ Glossary successfully resolved! ID: {new_glossary_id}")

    # 2. Import Terms
    print("📦 Importing Glossary Terms...")
    
    # Sort terms by length of fullyQualifiedName to ensure parents are created before children
    source_terms.sort(key=lambda t: len(t.get("fullyQualifiedName", "").split(".")))

    for term in source_terms:
        term_name = term.get("name")
        
        term_payload = {
            "name": term_name,
            "displayName": term.get("displayName"),
            "description": term.get("description"),
            "glossary": new_glossary_name,
            "owners": [{"id": owner_id, "type": "user"}],
            "synonyms": term.get("synonyms", []),
            "relatedTerms": term.get("relatedTerms", []),
            "references": term.get("references", []),
            "mutuallyExclusive": term.get("mutuallyExclusive", False)
        }
        
        parent = term.get("parent")
        if parent:
            term_payload["parent"] = parent.get("fullyQualifiedName")

        print(f"  ➡️ Importing Term: {term_name}")
        term_response = client._make_request("POST", "/glossaryTerms", json=term_payload)
        if term_response is not None and term_response.status_code in [200, 201]:
             print("    ✅ Success")
        elif term_response is not None and (
            term_response.status_code == 409 or 
            (term_response.status_code == 400 and "already exists" in term_response.text)
        ):
             print("    ℹ️ Already exists (skipping)")
        else:
             status_code = term_response.status_code if term_response is not None else "N/A"
             err_msg = "No Response"
             if term_response is not None:
                 try:
                     err_msg = term_response.json().get("message", term_response.text)
                 except Exception:
                     err_msg = term_response.text
             print(f"    ❌ Failed with status {status_code}: {err_msg}")

    print("✨ Glossary import process complete.")

if __name__ == "__main__":
    main()

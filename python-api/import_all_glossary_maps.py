#!/usr/bin/env python3
import os
import sys
import subprocess
import glob

def main():
    json_dir_base = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    target_dir = os.path.join(json_dir_base, "glossaryMap")
    
    if not os.path.isdir(target_dir):
        print(f"❌ Error: Directory '{target_dir}' does not exist.")
        sys.exit(1)

    json_files = glob.glob(os.path.join(target_dir, "*.json"))
    
    if not json_files:
        print(f"ℹ️ No JSON files found in {target_dir}")
        return

    print(f"🚀 Found {len(json_files)} Glossary Map file(s) to apply.")
    
    script_path = os.path.join(os.path.dirname(__file__), "apply_service_glossary_maps.py")

    for file_path in json_files:
        print(f"\n--- Applying Map: {os.path.basename(file_path)} ---")
        result = subprocess.run([sys.executable, script_path, file_path])
        if result.returncode != 0:
            print(f"⚠️ Warning: Applying {file_path} failed with exit code {result.returncode}")

    print("\n✅ Bulk Glossary Map restoration complete.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import subprocess
import glob

def main():
    json_dir_base = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    target_dir = os.path.join(json_dir_base, "glossary")
    
    if not os.path.isdir(target_dir):
        print(f"❌ Error: Directory '{target_dir}' does not exist.")
        sys.exit(1)

    json_files = glob.glob(os.path.join(target_dir, "*.json"))
    
    if not json_files:
        print(f"ℹ️ No JSON files found in {target_dir}")
        return

    print(f"🚀 Found {len(json_files)} Glossary file(s) to import.")
    
    script_path = os.path.join(os.path.dirname(__file__), "import_glossary.py")

    for file_path in json_files:
        print(f"\n--- Importing: {os.path.basename(file_path)} ---")
        result = subprocess.run([sys.executable, script_path, file_path])
        if result.returncode != 0:
            print(f"⚠️ Warning: Import of {file_path} failed with exit code {result.returncode}")

    print("\n✅ Bulk Glossary import complete.")

if __name__ == "__main__":
    main()

#!/bin/bash

# Ensure we are in the script's directory (essential for cron)
cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi
echo "Refreshing Collate Documentation..."
python3 smart_split_llms.py https://docs.getcollate.io/llms-full.txt

echo -e "\nRefreshing OpenMetadata Documentation..."
python3 smart_split_llms.py https://docs.open-metadata.org/llms-full.txt

echo -e "\nAll files successfully synced to Google Drive!"

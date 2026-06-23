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

echo -e "\nRefreshing Unsplit Documentation..."
python3 smart_split_llms.py https://docs.getcollate.io/llms.txt --no-split
python3 smart_split_llms.py https://www.getcollate.io/llms-full.txt --no-split
python3 smart_split_llms.py https://www.getcollate.io/llms.txt --no-split

echo -e "\nAll files successfully synced to Google Drive!"

#!/bin/bash

# 1. Clean up old environments
# rm -rf venv-collate

# 2. Create venv using Python 3.11  (I used 3.11.14)
# python3 -m venv venv-collate

# 3. Activate
source venv-collate/bin/activate

# 4. Upgrade pip
# pip install --upgrade pip
pip install cachetools
pip install pandas
# 5. Install the specific version with connectors
# We use ==1.11.4 to match your server
pip install "openmetadata-ingestion[snowflake]==1.11.4.0" --force-reinstall
pip install "openmetadata-ingestion[cockroach]==1.11.4.0"

# 6. Verify
metadata --version

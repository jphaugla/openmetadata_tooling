#!/bin/bash

# 1. Clean up old environments
# rm -rf venv-collate

# 2. Create venv using Python 3.11  (I used 3.11.14)
# python3 -m venv venv-collate

# 3. Activate
source venv-collate/bin/activate
COLLATE_VERSION=1.12.10

# 4. Upgrade pip
# pip install --upgrade pip
pip install cachetools
pip install pandas
# 5. Install the specific version with connectors
# We use ==1.11.4 to match your server
pip install "openmetadata-ingestion==${COLLATE_VERSION}" --force-reinstall
pip install "openmetadata-ingestion[snowflake]==${COLLATE_VERSION}" --force-reinstall
pip install "openmetadata-ingestion[cockroach]==${COLLATE_VERSION}"

# 6. Verify
metadata --version

# OpenMetadata Ingestion Framework

This directory contains the scripts and configurations for running external metadata ingestion pipelines into OpenMetadata/Collate using the official Python Ingestion Framework.

For full documentation on running external ingestion via the CLI, please refer to the [Collate External Ingestion Documentation](https://docs.getcollate.io/deployment/ingestion/external).

---

## Prerequisites & Environment Variables

The ingestion YAML configuration files are designed to dynamically read secrets from your environment to avoid hardcoding sensitive information.

Before running the ingestion, ensure the following environment variables are set in your terminal:

```bash
# Collate API setup
export API_COLLATE_BASE="https://your-collate-domain.com/api"
export TOKEN="your_collate_jwt_token"

# Database Specific Secrets (e.g. for CockroachDB)
export MY_CRDB_USER="your_db_username"
export MY_CRDB_PASS="your_db_password"
```

*(You can store these in your local hidden script like `~/.collate/setEnv.sh` and source it!)*

---

## Setup

The `install.sh` script automates the creation of a virtual environment and installs the required `openmetadata-ingestion` dependencies. 

> **Important**: The ingestion framework version MUST match your OpenMetadata/Collate server version. This script locks the version to `1.11.4.0`.

To install the dependencies:
```bash
cd ingestionFramework/
./install.sh
```
*(Note: If it's your first time running this, you may need to uncomment the `python3 -m venv venv-collate` line in `install.sh` to create the virtual environment).*

---

## Usage

Once your virtual environment is activated and your environment variables are exported, you can run the ingestion pipeline.

To run the sample CockroachDB ingestion:
```bash
./run_ingest.sh
```

This script simply executes:
```bash
metadata ingest -c crdb_ingest_movr.yaml
```

### Configuration Files
- `crdb_ingest_movr.yaml`: An example ingestion recipe connecting to a local CockroachDB `movr` database, parsing the `public` schema, and pushing the extracted metadata directly to the Collate server.

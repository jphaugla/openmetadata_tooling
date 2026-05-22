# Python API Directory

This directory contains Python scripts for interacting with the OpenMetadata API. These scripts provide a robust way to automate catalog operations, migrate metadata, and manage ingestion pipelines.
The openmetadata api documenation is [here](https://docs.open-metadata.org/v1.12.x/api-reference/main-concepts/metadata-standard/apis)
The collate api documenation is [here](https://docs.getcollate.io/connectors/api)

## 📁 Directory Structure

*   **/ (Main Directory)**: General-purpose utility scripts. These are designed to be reusable across different environments and services (usually by taking arguments).
*   **[examples/](file:///Users/jasonhaugland/gits/openmetadata_tooling/python-api/examples/)**: One-off, demo-specific, or hardcoded scripts. Use these as templates for your own custom automation.

## 🚀 Prerequisites

This directory uses **pyenv** for Python version management and a **virtual environment** for dependencies.

**1. Set up Python Version:**
```bash
# pyenv will automatically select the version from .python-version
pyenv install 3.11.14
```

**2. Create and Activate Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
All scripts require the following environment variables (set them via `source ~/.collate/setJson.sh` or manual export):

| Variable | Required | Description |
|---|---|---|
| `API_BASE` | ✅ | Base URL (e.g., `https://your-org.getcollate.io/api/v1`) |
| `TOKEN` | ✅ | JWT or Bot Token |
| `OWNER_ID` | Optional | UUID for the user who will own imported entities |
| `JSON_DIR` | ✅ | Path to metadata storage folder (e.g., `../json/`) |

---

## 🛠️ Main Utility Scripts

### Core Client
*   **`om_client.py`**: Shared base class that handles authentication, URL building, and common API methods.

### Bulk Operations
These scripts loop through your `$JSON_DIR` subdirectories to import metadata in mass.

| Script | Description |
|---|---|
| `import_all_database_services.py` | Imports all `.json` files in `databaseService/` |
| `import_all_glossaries.py` | Imports all `.json` files in `glossary/` |
| `import_all_glossary_maps.py` | Applies all tag/glossary mappings in `glossaryMap/` |
| `import_all_pipelines.py` | Imports all `.json` files in `pipelines/` |
| `deploy_all_pipelines.py` | Deploys every ingestion pipeline currently defined in the system |
| `import_all_search_services.py` | Imports all `.json` files in `searchService/` |

### Service & Pipeline Management
| Script | Description |
|---|---|
| `get_db_service.py <name>` | Exports a Database Service definition to JSON |
| `import_db_service.py <file>` | Imports a Database Service from JSON |
| `get_dashboard_service.py <name>` | Exports a Dashboard Service definition to JSON |
| `import_dashboard_service.py <file>` | Imports a Dashboard Service from JSON |
| `list_services.py` | Lists all defined services with their IDs and Status |
| `delete_service.py <name>` | Hard-deletes a service and all its children (recursive) |
| 'get_service_pipeline_status.py <service_name>` | Maps all ingestion pipelines for a service with explicit Pipeline Name, ID, FQN, Type, and recent history logs. |
| `get_pipeline_logs.py <id_or_fqn> [run_id]` | Resolves a pipeline to its FQN, extracts orchestrator execution logs, and handles Argo step-nodes automatically. |
| `run_service_pipelines.py <name>` | Triggers Metadata, wait for success, then triggers dependents |
| `deploy_service_pipelines.py <name>` | Deploys all ingestion pipelines for a specific service |
| `get_ingestion_ip.py` | Returns the Ingestion IP and whitelisting explanation |
| `kill_pipeline.py <name_or_fqn>` | Resolves a pipeline Name or FQN string to its database GUID ID and sends a terminating KILL signal. |

### Glossary & Lineage (Generic)
| Script | Description |
|---|---|
| `get_glossary.py <name>` | Exports a Glossary and its terms |
| `import_glossary.py <file>` | Imports a Glossary (supports hierarchical terms) |
| `get_service_glossary_maps.py` | Exports tag/glossary mappings for a service |
| `apply_service_glossary_maps.py` | Re-applies mappings to entities on a target instance |
| `export_lineage.py <service>` | Exports all lineage edges for a service |
| `import_lineage.py <service>` | Re-creates lineage edges from a JSON export |

---

## 🧪 Example & Demo Scripts (`examples/`)

These scripts are located in the [examples/](file:///Users/jasonhaugland/gits/openmetadata_tooling/python-api/examples/) subdirectory. They often contains hardcoded values used for specific demo scenarios.

### S3 & Snowflake Demo Workarounds
| Script | Description |
|---|---|
| `add_s3_column_lineage.py` | **Workaround**: Forcefully injects Column Lineage between S3 and Snowflake |
| `restore_s3_container.py` | **Fix**: Restores the S3 bucket if the native agent soft-deletes it |
| `upload_dbt_artifacts.py` | Uploads `manifest.json`, `catalog.json`, etc. to S3 for dbt ingestion |
| `inspect_s3_security.py` | Inspects encryption, policies, and public access settings of the demo bucket |
| `create_s3_container.py` | Programmatically creates a container if the agent fails to discover it |

### CockroachDB Demo Suites
| Script | Description |
|---|---|
| `suite_run_pipelines_cockroach.py` | Orchestrates the full sequential run of the CRDB demo |
| `suite_add_cockroach.py` | Mass-imports the CRDB service stack from JSON |
| `suite_delete_cockroach.py` | Wipes the entire CRDB demo stack clean |
| `suite_fix_crdb_privileges.py` | Patches `allow_unsafe_internals` on all CRDB connections |

### Miscellaneous Examples
| Script | Description |
|---|---|
| `sync_all_lineage.py` | Syncs dbt and native lineage (used for dbt-to-S3-to-Snowflake demo) |
| `check_lineage.py` | Fetches a JSON dump of upstream/downstream lineage for a specific table |
| `compare_counts.py` | Validates synchronization between the DB and the Search Index |
| `add_cdc_pipeline.py` | Example of creating an Ingestion Pipeline entity via API |
| `add_er_lineage.py` | Manual injection of Entity-Relationship lineage |

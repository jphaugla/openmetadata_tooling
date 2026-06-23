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

**Core (all scripts):**

| Variable | Required | Description |
|---|---|---|
| `API_BASE` | ✅ | Base URL (e.g., `https://your-org.getcollate.io/api/v1`) |
| `TOKEN` | ✅ | JWT or Bot Token |
| `OWNER_ID` | Optional | UUID for the user who will own imported entities |
| `JSON_DIR` | ✅ | Path to metadata storage folder (e.g., `../json/`) |

**S3 export scripts (`export_audit_logs.py`, `export_events_to_s3.py`):**

| Variable | Required | Description |
|---|---|---|
| `S3_BUCKET` | ✅ (unless `--dry-run`) | Destination S3 bucket |
| `S3_KEY_PREFIX` | Optional | Folder prefix inside the bucket (default: `""`) |
| `STATE_DIR` | Optional | Directory for the state file (default: `.`) |
| `DRY_RUN` | Optional | Set to `true` to print output without writing to S3 |
| `AUDIT_LOG_TOKEN` | ✅ (audit logs only) | Separate token with `AuditLogs` permission — the ingestion-bot does **not** have this by default. Grant it via Settings → Access Control → Roles. |

---

## 🛠️ Main Utility Scripts

### Core Client
*   **`om_client.py`**: Shared base class that handles authentication, URL building, and common API methods.

### User & Access Diagnostics
| Script | Description |
|---|---|
| `get_user_detail.py <username_or_displayname>` | Fetches full user details (id, roles, teams, isAdmin, isBot) and resolves each role → policy → operations by ID to show the exact set of allowed operations. Falls back to displayName search if name lookup fails; exits with a duplicate list if multiple users share a displayName. Prints a `🟢/🔴 AuditLogs: GRANTED/NOT GRANTED` summary for quick bot permission validation. |
| `list_roles.py` | Lists all defined roles with their IDs |
| `list_users.py` | Lists all users with basic metadata |

### S3 Data Export
Incremental exporters that track state so each run picks up only new entries. State is saved to `state_<type>.txt` in `STATE_DIR` (default: current directory). Supports `--dry-run` to validate output without writing to S3.

| Script | Description |
|---|---|
| `export_audit_logs.py` | Exports audit log entries from `/v1/audit/logs` to `s3://<S3_BUCKET>/<S3_KEY_PREFIX>audit_logs/audit_logs_<timestamp>.jsonl`. Requires `AUDIT_LOG_TOKEN` (separate from `TOKEN`) with the `AuditLogs` permission. Supports `--all`, `--start-date YYYY-MM-DD`, `--skip-state`, `--dry-run`. |
| `export_events_to_s3.py` | Exports metadata change events from `/v1/events` (all entity types) to `s3://<S3_BUCKET>/<S3_KEY_PREFIX>change_events/events_<timestamp>.jsonl`. Uses timestamp-based pagination. Supports same flags as above. |

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
| `import_glossary.py <file>` | Imports a Glossary from a JSON file exported by `get_glossary.py`. Creates the glossary (or resolves an existing one on 409) then imports all terms in dependency order (parents before children) using `fullyQualifiedName` depth sorting. Skips already-existing terms. Requires `OWNER_ID`. |
| `get_service_glossary_maps.py` | Exports tag/glossary mappings for a service |
| `apply_service_glossary_maps.py` | Re-applies mappings to entities on a target instance |
| `export_lineage.py <service>` | Exports all lineage edges for a service |
| `import_lineage.py <service>` | Re-creates lineage edges from a JSON export |

### Maintenance & Cleanup
| Script | Description |
|---|---|
| `clear_service_descriptions.py <service_name>` | Clears all table-level and column-level descriptions for every table in a service, resetting them to an empty string. Useful for demo resets or before re-running AI description generation. Accepts `--contains <substring>` to scope the wipe to matching table names only. Defaults to the `Enterprise_SE` service if no name is provided. |

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

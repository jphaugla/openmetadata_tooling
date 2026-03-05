# Python API Directory

This directory contains Python scripts for interacting with the OpenMetadata API. These scripts are the Python equivalents of the tools found in the `../api/` (Bash) directory, providing the same functionality with better handling of service names with spaces, robust JSON parsing, and cleaner error handling — all without needing `jq`.

JSON definitions used and produced by these scripts are stored in the directory specified by the `JSON_DIR` environment variable (defaults to `../json/`). For security, it is recommended to keep this directory outside of your git repository.

## API Documentation

*   [OpenMetadata API Documentation](https://docs.open-metadata.org/v1.6.x/main-concepts/metadata-standard/apis) - Official API reference.
*   [OpenMetadata Schemas](https://github.com/open-metadata/OpenMetadata/tree/main/openmetadata-spec/src/main/resources/json/schema) - JSON Schemas for metadata entities.

## Prerequisites

This directory uses **pyenv** for Python version management and a **virtual environment** for dependencies.

**1. Set up Python Version:**
```bash
# Ensure you have the version installed
pyenv install 3.11.14
# pyenv will automatically select the version from .python-version
```

**2. Create and Activate Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate
```

**3. Install Dependencies:**
```bash
pip install -r requirements.txt
```

All scripts read the following environment variables:

| Variable | Required | Description |
|---|---|---|
| `API_BASE` | ✅ | Base URL of the OpenMetadata API (e.g., `http://localhost:8585/api/v1`) |
| `TOKEN` | ✅ | A valid JWT or Bot Token for authentication |
| `OWNER_ID` | Import Scripts Only | UUID of the user who will own the imported entities |
| `SLEEP_SECONDS` | Optional | For status check scripts, interval between checks (default: 10) |
| `MAX_RETRIES` | Optional | For status check scripts, maximum number of attempts (default: 30) |
| `JSON_DIR` | Highly Recommended | Path to storage directory (e.g., `~/.collate/json/`) |

```bash
export API_BASE="https://source.open-metadata.org/api/v1"
export TOKEN="<your_token>"
export OWNER_ID="<owner_uuid>"
export JSON_DIR="~/.collate/json/"
mkdir -p "$JSON_DIR"
```

## Migration Workflow Example

Demonstrates exporting a `RedshiftProd` service from a **Source** instance and importing to a **Target** instance.

### 1. Export from Source
```bash
export API_BASE="https://source.open-metadata.org/api/v1"
export TOKEN="<source_token>"

# Export Service Definition
# Output: ../json/RedshiftProd.json
python get_db_service.py "RedshiftProd"

# Export Pipelines
# Output: ../json/RedshiftProd_pipelines.json
python get_pipelines.py "RedshiftProd"
```

### 2. Import to Target
```bash
export API_BASE="https://target.open-metadata.org/api/v1"
export TOKEN="<target_token>"
export OWNER_ID="<target_owner_uuid>"

python import_db_service.py "$JSON_DIR/RedshiftProd.json"
python import_pipelines.py "$JSON_DIR/RedshiftProd_pipelines.json"
```

## Scripts Description

### Core Client
*   **`om_client.py`**: Shared base class. Handles authentication headers, URL building, and provides common methods (`trigger_pipeline`, `deploy_pipeline`, `get_pipelines_for_service`, etc.). All other scripts import this.

---

### Orchestration Suites
Scripts that orchestrate a full sequence of operations for the CockroachDB suite.

| Script | Description |
|---|---|
| `suite_get_cockroach.py` | Exports all CockroachDB services and their pipelines to `../json/` |
| `suite_add_cockroach.py` | Imports from JSON, runs pre-import cleanup first |
| `suite_deploy_pipelines_cockroach.py` | Deploys all ingestion pipelines for the suite |
| `suite_run_pipelines_cockroach.py` | Runs each service (Metadata-first, then dependents) sequentially |
| `suite_delete_cockroach.py` | Deletes all CockroachDB services and pipelines |
| `suite_fix_crdb_privileges.py` | Applies `allow_unsafe_internals=true` to all CockroachDB connections |
| `suite_update_host_port_cockroach.py <host:port>` | Updates `hostPort` for all CockroachDB services |

---

### Service Management (Database & Search)

| Script | Description |
|---|---|
| `get_db_service.py <service_name>` | Exports a Database Service to `../json/<service_name>.json` |
| `import_db_service.py <file.json>` | Imports a Database Service from a JSON file |
| `delete_service.py <service_name>` | Hard-deletes a Database Service by name (recursive) |
| `list_services.py` | Lists all defined Database Services |
| `get_search_service.py <service_name>` | Exports a Search Service to `../json/<service_name>.json` |
| `import_search_service.py <file.json>` | Imports a Search Service from a JSON file |

---

### Pipeline Management

| Script | Description |
|---|---|
| `get_pipelines.py <service_name>` | Exports all pipelines for a service to `../json/<service_name>_pipelines.json` |
| `import_pipelines.py <file.json>` | Imports pipelines from a JSON file |
| `deploy_service_pipelines.py <service_name>` | Deploys all pipelines for a service to the Kubernetes orchestrator |
| `run_service_pipelines.py <service_name>` | Triggers Metadata pipeline, waits for success, then triggers dependents |
| `kill_pipeline.py <pipeline_name>` | Sends a kill signal to a running or stuck pipeline |
| `delete_pipelines.py <service_name>` | Hard-deletes all ingestion pipelines for a service |
| `delete_pipeline_service.py <service_name>` | Hard-deletes a Pipeline Service entity |
| `delete_entity_pipeline.py <pipeline_name>` | Hard-deletes a standard pipeline entity (e.g., a CDC pipeline) |
| `add_cdc_pipeline.py` | Creates the `movr_cdc` CDC pipeline entity for CockroachDB |

---

### Glossary & Lineage

| Script | Description |
|---|---|
| `get_glossary.py <glossary_name>` | Exports a Glossary and its terms to `../json/<glossary>_glossary.json` |
| `import_glossary.py <file.json>` | Imports a Glossary and all its terms (sorted by hierarchy depth) |
| `get_service_glossary_maps.py <service_name>` | Exports tag mappings for a service to `../json/<service>_glossary_map.json` |
| `apply_service_glossary_maps.py <file.json>` | Applies tag mappings back to entities on a target instance |
| `add_er_lineage.py` | Adds ER lineage edges between CockroachDB movr tables |
| `check_lineage.py [table_fqn]` | Fetches upstream/downstream lineage for a table (default: `movr.rides`) |

---

### Connection Management

| Script | Description |
|---|---|
| `update_db_service_host_port.py <service_name> <host:port>` | Updates the `hostPort` for a specific Database Service |
| `patch_crdb_connection_options.py <service_name>` | Applies `allow_unsafe_internals=true` to a single CockroachDB service connection |

---

### Utilities

| Script | Description |
|---|---|
| `check_server_status.py` | Polls the OM server until it reports healthy; uses `SLEEP_SECONDS` and `MAX_RETRIES` |
| `check_collate_status.py` | Like `check_server_status.py` but ignores non-critical migration failures for Collate SaaS |
| `get_owner_id.py <owner_name>` | Resolves an owner's display name to their UUID |
| `get_table_metadata.py <table_fqn>` | Fetches tags and extension metadata for a specific table FQN |
| `list_users.py` | Lists all users with their names, IDs, and admin/bot flags |
| `list_roles.py` | Lists all roles with their IDs |
| `compare_counts.py` | Compares user counts between the OM database and the Elasticsearch index |
| `delete_user_team.py` | Hard-deletes the configured user (`jason.haugland`) and team (`Solution Architects`) |

# API Directory

This directory contains utility scripts for interacting with the OpenMetadata API. These scripts are used for exporting, importing, and managing metadata entities such as Database Services, Pipelines, and Glossaries.

The JSON definitions used and produced by these scripts are stored in the `json/` subdirectory.

## Link to API Documentation

*   [OpenMetadata API Documentation](https://docs.open-metadata.org/v1.6.x/main-concepts/metadata-standard/apis) - Official API reference for OpenMetadata (Collate).
*   [OpenMetadata Schemas](https://github.com/open-metadata/OpenMetadata/tree/main/openmetadata-spec/src/main/resources/json/schema) - JSON Schemas for metadata entities.

## Prerequisites

The scripts in this directory rely on the following environment variables being set in your shell:

*   **`API_BASE`**: The base URL of the OpenMetadata API (e.g., `https://sandbox.open-metadata.org/api/v1`).
*   **`TOKEN`**: A valid JWT or Bot Token for authentication.
*   **`OWNER_ID`**: (Required for Imports) The UUID of the user who will own the imported entities.

Ensure these are exported before running any scripts:
```bash
export API_BASE="https://source.open-metadata.org/api/v1"
export TOKEN="<source_token>"
export OWNER_ID="<owner_uuid>"
```

## Migration Workflow Example

This flow demonstrates how to export a "RedshiftProd" database service from a **Source** instance and move it to a **Target** instance.

### 1. Export from Source
Set your environment to the Source instance.
```bash
# Set Source Environment
export API_BASE="https://source.open-metadata.org/api/v1"
export TOKEN="<source_token>"

# Export Service Definition
./getDBService.sh "RedshiftProd"
# Output: json/RedshiftProd.json

# Export Pipelines (Ingestion)
./getPipelines.sh "RedshiftProd"
# Output: json/RedshiftProd_pipelines.json
```

### 2. Import to Target
Switch your environment to the Target instance.
```bash
# Set Target Environment
export API_BASE="https://target.open-metadata.org/api/v1"
export TOKEN="<target_token>"
export OWNER_ID="<target_owner_uuid>" # Owner on the target system

# Import Service
./importDBService.sh "json/RedshiftProd.json"

# Import Pipelines
./importPipelines.sh "json/RedshiftProd_pipelines.json"
```

## Scripts Description

### Orchestration Suites
Scripts that run a sequence of operations for specific recurring tasks.
*   **`suite_get_cockroach.sh`**: Exports multiple CockroachDB services and their pipelines.
*   **`suite_add_cockroach.sh`**: Imports the suite of CockroachDB services and pipelines using the JSON files in `json/`.
*   **`suite_delete_cockroach.sh`**: Deletes the CockroachDB services defined in the suite.

### Service Management (Database & Search)
*   **`getDBService.sh <service_name>`**: Exports a Database Service definition to `json/<service_name>.json`.
*   **`importDBService.sh <file.json>`**: Imports a Database Service from a JSON file.
*   **`delete_service.sh <service_name>`**: Deletes a service (generic) by name.
*   **`list_services.sh`**: Lists available services.
*   **`getSearchService.sh <service_name>`**: Exports a Search Service definition to `json/<service_name>.json`.
*   **`importSearchService.sh <file.json>`**: Imports a Search Service.
*   **`cockroach_db_add.sh`**: Helper to add a specific CockroachDB service.
*   **`cockroach_db_delete.sh`**: Helper to delete a specific CockroachDB service.

### Pipeline Management
*   **`getPipelines.sh <service_name>`**: Exports all pipelines associated with a service to `json/<service_name>_pipelines.json`.
*   **`importPipelines.sh <file.json>`**: Imports pipelines from a JSON file.
*   **`addCDCPipeline.sh`**: Creates the `movr_cdc` pipeline entity.
*   **`deletePipelineService.sh <service_name>`**: Deletes a target Pipeline Service and its pipelines.
*   **`deleteEntityPipeline.sh <fqn>`**: Deletes a standard pipeline entity (e.g., `Cockroach_to_Postgres_CDC.movr_cdc`) using hard delete.
*   **`deletePipelines.sh`**: Deletes specific pipelines.

### Glossary & Lineage
*   **`getGlossary.sh <glossary_name>`**: Exports a Glossary and its terms to `json/<glossary>_glossary.json`.
*   **`importGlossary.sh <file.json>`**: Imports a Glossary and terms.
*   **`getServiceGlossaryMaps.sh <service_name>`**: Exports the tagging mapping (Glossary Terms -> Table/Column) for a service to `json/<service_name>_glossary_map.json`.
*   **`applyServiceGlossaryMaps.sh <file.json>`**: Applies the tagging mapping to a service.
*   **`addERLineage.sh`**: Adds entity-relationship lineage.
*   **`checkLineage.sh`**: Checks lineage status.

### Utilities
*   **`getOwnerID.sh`**: Resolves an Owner Name to an ID.
*   **`list_roles.sh`**: Lists available roles.
*   **`delete_user_team.sh`**: Deletes a user or team.
*   **`compare_counts.sh`**: Compares counts of entities (validation).

# Jupyter Python SDK Demo

This directory contains a suite of Jupyter notebooks and scripts designed to demonstrate advanced usage of the **OpenMetadata Python SDK** with a focus on **CockroachDB** integration and **programmatic Lineage** management.

## Overview

The demo showcases how to leverage the full power of the Python SDK for:
1. **Metadata Discovery**: Efficiently exploring Tables, Services, Glossaries, and Users.
2. **Programmatic Lineage**: Creating and managing lineage relationships between CockroachDB entities using native SDK objects.
3. **Advanced Operations**: Listing roles, ingestion pipelines, and performing deep entity inspection.

## Prerequisites

- **OpenMetadata/Collate Instance**: An active instance must be reachable.
- **CockroachDB**: The lineage and discovery examples are specifically configured for CockroachDB services.
- **Environment Variables**: Ensure `TOKEN` and `API_COLLATE_BASE` are set in your environment (typically via `~/.collate/setEnv.sh`).

## Setup Instructions

### 1. Environment Installation
Install the specialized Python environment (version 3.10) and required dependencies:

```bash
./install.sh
```
This script performs several critical steps:
- Creates a virtual environment named `colat-env`.
- **Lineage Parser Fix**: Force-reinstalls a specific version of `collate-sqllineage` and creates a namespace bridge to ensure proper lineage parsing for the current OpenMetadata version.
- Installs necessary integrations for Postgres and CockroachDB.
- Registers the Jupyter kernel `Python (3.10) using SDK`.

## Running the Demo

To launch the Jupyter Lab environment:

```bash
./exec.sh
```
This script ensures your OpenMetadata environment variables are active and launches the notebook server.

## Key Files

### Scripts
- [requirements.txt](jupyter_python_sdk/requirements.txt): Lists SDK dependencies, including `openmetadata-ingestion[db,cockroachdb,profiler,classification]`.
- [install.sh](jupyter_python_sdk/install.sh): Specialized setup script with lineage parsing repairs.
- [exec.sh](jupyter_python_sdk/exec.sh): Convenience launcher for the demo.
- [update_notebook.py](jupyter_python_sdk/update_notebook.py): Utility to programmatically update notebooks with native SDK code cells.

### Jupyter Notebooks
- [FQN research.ipynb](jupyter_python_sdk/FQN%20research.ipynb): 
    - **Entity Exploration**: Fetching and inspecting Database Services, Glossaries, and User roles.
    - **Lineage Management**: Step-by-step examples of creating lineage between CockroachDB tables.
- [test_workflow.ipynb](jupyter_python_sdk/test_workflow.ipynb): Demonstration of end-to-end data ingestion and profiling.
- [test_dataframe.ipynb](jupyter_python_sdk/test_dataframe.ipynb): Examples of shift-left validation and data quality checks using the SDK.

## Troubleshooting

- **Lineage Parsing Errors**: If lineage relationships fail to render, verify that the `sqllineage` bridge was successfully created in your site-packages (refer to the `install.sh` output).
- **Service Connectivity**: ensure your `API_COLLATE_BASE` includes the `/api/v1` suffix and that your JWT `TOKEN` has sufficient permissions for lineage and entity creation.

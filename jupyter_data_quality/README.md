# Jupyter Data Quality Demo

This directory contains a set of Jupyter notebooks and scripts designed to demonstrate **Data Quality (DQ)** capabilities using **OpenMetadata** and **Collate**.

## Overview

The demo showcases two primary workflows:
1. **End-to-End Ingestion & DQ**: Ingesting data from external sources into a Postgres database and running DQ tests against the resulting tables.
2. **Shift-Left Validation**: Using the `DataFrameValidator` to run DQ tests directly on Pandas DataFrames during an ETL process, before the data is committed to the database.

## Prerequisites

- **OpenMetadata/Collate Instance**: An active instance must be running.
- **Postgres Database**: The demo requires a local Postgres instance (configured via Docker).
- **Environment Variables**: Ensure `TOKEN` (your OpenMetadata JWT) and `API_COLLATE_BASE` (OpenMetadata URL) are properly set (typically in `~/.collate/setEnv.sh`).

## Setup Instructions

1. **Database Setup**
> [!IMPORTANT]
> This demo requires the `raw` and `stg` databases to be initialized in Postgres. **You must run the provided setup script before proceeding:**

```bash
# From the project root
./docker/data_quality_demo.sh
```
This script creates the necessary databases, roles, and initial tables (`taxi_yellow` and `dw_taxi_trips`).

### 2. Environment Installation
Install the required Python environment and dependencies:

```bash
./install.sh
```
This script:
- Creates a virtual environment `dq-lean-env`.
- Installs `openmetadata-ingestion` (version 1.11.8) and DQ utilities.
- Creates a "Namespace Bridge" for Lineage compatibility.
- Registers the Jupyter kernel `Python (Collate-1.11.8-DQ-Lean)`.

## Running the Demo

To start the Jupyter Lab environment:

```bash
./exec.sh
```
This script activates the `dq-lean-env` and launches Jupyter Lab.

## Key Files

### Scripts
- [requirements.txt](jupyter_data_quality/requirements.txt): Lists all Python dependencies, including `openmetadata-ingestion[profiler,pandas,postgres]`.
- [install.sh](jupyter_data_quality/install.sh): Automated installation script for the local environment.
- [exec.sh](jupyter_data_quality/exec.sh): Convenience script to launch the demo.

### Jupyter Notebooks
- [test_workflow.ipynb](jupyter_data_quality/test_workflow.ipynb): 
    - Loads NYC Taxi data (Parquet/CSV).
    - Performs an ETL and loads results into the `raw.public.taxi_yellow` table.
    - Runs Data Quality tests defined in OpenMetadata against the table.
- [test_dataframe.ipynb](jupyter_data_quality/test_dataframe.ipynb):
    - Demonstrates **Shift-Left** validation.
    - Uses `DataFrameValidator` to validate Pandas DataFrames *before* loading into the `stg.public.dw_taxi_trips` table.
    - Shows how to publish DQ results back to OpenMetadata.

## Troubleshooting

- **Lineage Parser**: The `install.sh` script creates a bridge for `sqllineage`. If you encounter lineage parsing errors, ensure the bridge was created correctly in your site-packages.
- **Connection Errors**: Verify that your OpenMetadata instance is reachable at the URL specified in `API_COLLATE_BASE`.

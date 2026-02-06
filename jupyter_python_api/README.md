# Jupyter Python API Demo

This directory contains a Jupyter notebook and supporting scripts for interacting directly with the **OpenMetadata API** using Python's `requests` library.

## Overview

Unlike other demos that might use the OpenMetadata SDK, this demo focuses on **direct REST API calls**. This is useful for:
- Understanding the underlying API structure.
- Performing operations not yet supported by the SDK.
- Lightweight interactions without heavy dependencies.

## Setup Instructions

### 1. Credentials Setup
The scripts expect your OpenMetadata credentials to be defined in your environment or a secure configuration file (e.g., `~/.collate/setEnv.sh`). Specifically, it looks for:
- `TOKEN`: Your JWT token.
- `API_COLLATE_BASE`: The base URL of your OpenMetadata instance (e.g., `your-instance-url/api/v1`).

### 2. Environment Installation
Install the required Python environment (version 3.11 recommended):

```bash
./install.sh
```
This script:
- Creates a virtual environment `colat-env`.
- Installs dependencies from `requirements.txt` (`requests`, `python-dotenv`, `ipykernel`).
- Registers the Jupyter kernel `Python (3.11) just using api`.

## Running the Demo

To launch Jupyter Lab:

```bash
./exec.sh
```
This script ensures your environment variables are loaded and launches the notebook server.

## Key Files

- [requirements.txt](jupyter_python_api/requirements.txt): Minimal dependencies for REST API calls.
- [install.sh](jupyter_python_api/install.sh): Setup script for the Python environment.
- [exec.sh](jupyter_python_api/exec.sh): Launches the Jupyter environment.
- [PythonWrappedAPIcalls.ipynb](jupyter_python_api/PythonWrappedAPIcalls.ipynb):
    - **Metadata Retrieval**: Examples of fetching table entities by their Fully Qualified Name (FQN).
    - **Search Queries**: Demonstrates how to use the search endpoint to find entities based on schema names or other criteria.

## Important Notes

- **URL Handling**: The notebooks use the `API_BASE` or `API_COLLATE_BASE` environment variables. Ensure these point to the `/api/v1` (or relevant version) suffix of your OpenMetadata instance.
- **Authentication**: All calls require a valid JWT token passed in the `Authorization: Bearer <TOKEN>` header.

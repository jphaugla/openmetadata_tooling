# AI SDK Python Example

This directory contains a Python implementation of the [OpenMetadata AI SDK](https://github.com/open-metadata/ai-sdk) examples.

## Overview

The `run_agent.py` script demonstrates how to interact with Collate Agents (like `DataQualityPlannerAgent`) using the AI SDK. It includes examples of:
- Synchronous agent calls
- Real-time response streaming

## Setup

### Environment Variables

The example uses the same environment variables as the `mcp` and `python-api` directories. You can set them by sourcing your OpenMetadata environment script:

```bash
source ~/.openmetadata/setEnv.sh
```

The script specifically expects:
- `API_BASE`: The URL of your OpenMetadata/Collate instance (e.g., `http://localhost:8585/api/v1`)
- `TOKEN`: Your personal access token or bot JWT token.

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the example script:

```bash
python run_agent.py
```

## References

- [OpenMetadata AI SDK GitHub README](https://github.com/open-metadata/ai-sdk/blob/main/README.md) - Official documentation and more examples.

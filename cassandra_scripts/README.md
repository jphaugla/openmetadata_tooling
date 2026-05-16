# Cassandra Demo Setup

This directory contains scripts to set up a sample Cassandra environment for demonstration purposes, specifically tailored for integration with **Collate/OpenMetadata** using a **Hybrid Runner** on OrbStack.

## 📋 Overview

The demo environment simulates an e-commerce platform with the following keyspace and tables:

- **Keyspace**: `ecommerce_demo`
- **Tables**: `users`, `products`, `orders_by_user`, `inventory_log`.

## 🚀 How to Run the Demo

To set up the environment from scratch:

1. **Ensure Cassandra is installed**: `brew install cassandra`
2. **Run the setup script**: `./setup_demo.sh`
   - This starts Cassandra, creates the schema, and loads ~350 rows of data.

## ⌨️ How to Login

```bash
cqlsh -u cassandra -p cassandra -k ecommerce_demo
```

## 🔑 Authentication & Network Configuration

To allow a **Hybrid Runner** (on OrbStack) to connect to your local Mac, you **must** update your `cassandra.yaml` (usually at `/opt/homebrew/etc/cassandra/cassandra.yaml`):

```yaml
# Allow connections from all interfaces (including OrbStack)
rpc_address: 0.0.0.0

# Tell the runner to connect via the Mac's virtual address
broadcast_rpc_address: 192.168.50.93

# Keep gossip local to avoid startup errors
listen_address: 127.0.0.1
seed_provider:
    - ...
      parameters:
          - seeds: "127.0.0.1"
```

## 🌉 Connecting from Collate (Hybrid Runner)

When configuring the service in Collate:

- **Host And Port**: `host.orb.internal:9042`
- **Ingestion Runner**: Select your `orbstack-runner`.

> [!IMPORTANT]
> The **"Test Connection"** button in the Collate UI may still time out. This is because the test is often run from the Cloud, which cannot see your Mac. As long as your Hybrid Runner is selected, the actual ingestion will work.

## 🔍 Diagnostics

If you encounter connection issues, run the diagnostic script:

```bash
./test_connect.sh
```

This script enters your runner pod and attempts a direct TCP handshake with your Mac. If this script returns **SUCCESS**, your network path is correct.

## 🧹 Cleanup

To remove the demo keyspace and data: `./cleanup.sh`

## 🛠️ Files Included

- `schema.cql`: Database structure definitions.
- `generate_data.py`: Sample data generator.
- `insert_data.cql`: Generated data insertion script.
- `setup_demo.sh`: Master setup script.
- `cleanup.sh`: Teardown script.
- `test_connect.sh`: Diagnostic tool for Hybrid Runner connectivity.

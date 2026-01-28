# OpenMetadata Local Development Setup (Minikube)

This project automates the deployment of **OpenMetadata** and its dependencies (PostgreSQL, OpenSearch, Airflow) onto a local **Minikube** Kubernetes cluster.

It is designed to overcome common resource constraints and configuration "gotchas" when running the full stack locally on macOS.

## 📋 Prerequisites

Before running the installation script, ensure you have the following installed:

* **Docker Desktop** (Engine 20.10+)
* **Minikube** (v1.32+)
* **Helm** (v3.10+)
* **kubectl** (v1.25+)

### Hardware Requirements
This stack is resource-intensive. Your host machine should have at least:
* **RAM:** 16GB (24GB+ Recommended)
* **CPUs:** 4+ Cores

---

## 🚀 Quick Start

1.  **Start Minikube** with sufficient resources:
    ```bash
    # We recommend allocating 12GB RAM to the VM to prevent OOM Kills
    minikube start --driver=docker --memory=12288 --cpus=4
    ```

2.  **Run the Installer:**
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

3.  **Access the UI:**
    Once the installation completes, port-forward the OpenMetadata service:
    ```bash
    kubectl port-forward service/openmetadata 8585:8585
    ```
    * **URL:** [http://localhost:8585](http://localhost:8585)
    * **User:** `admin`
    * **Password:** `admin`

---

## 🏗️ Architecture & Kubernetes Situation

This deployment differs from the standard production Helm charts to optimize for a single-node local environment.

### 1. Storage Layer (PostgreSQL)
* **Chart:** `bitnami/postgresql`
* **Image Override:** `docker.getcollate.io/openmetadata/postgresql:1.11.6`
* **Reason:** We use the Bitnami chart for its reliability but swap the engine for the Collate custom image which contains necessary `pg_trgm` extensions pre-installed.
* 

### 2. Search Layer (OpenSearch)
* **Chart:** `openmetadata-dependencies` (Subchart)
* **Config:** Single-node mode with **Security Disabled**.
* **Critical Patches:**
    * `plugins.security.disabled: true`: Prevents connection refused errors from the main server.
    * `index.number_of_replicas: 0`: Forces indices to stay Green on a single node (Minikube).
    * **Memory:** Bumped to **2.5GB Limit** to prevent crash loops during startup.

### 3. Application Layer (OpenMetadata Server)
* **Chart:** `open-metadata/openmetadata`
* **Memory:** Bumped to **4GB Limit**.
* **Why?** Java applications expand to fill available heap. The standard 2GB limit often causes `OOMKilled` crashes during the initial Metadata extraction and indexing phase.

---

## 🛠️ The `install.sh` Script Explained

The `install.sh` script automates the complex sequencing required to bring this stack up safely.

| Step | Action | Description |
| :--- | :--- | :--- |
| **1. Cleanup** | `helm uninstall` & `delete pvc` | Wipes previous installations and, crucially, **deletes persistent volumes** to ensure no stale data locks corrupt the new run. |
| **2. Secrets** | `kubectl create secret` | Generates the necessary passwords for Postgres and Airflow. |
| **3. Postgres** | `helm install bitnami/postgresql` | Installs the database first. The script waits (`kubectl wait`) for this to be fully ready before proceeding. |
| **4. Config Gen** | `cat > deps.yaml` | Dynamically generates a YAML config file for OpenSearch. This avoids shell escaping issues with complex Helm flags. |
| **5. Dependencies** | `helm install dependencies` | Installs OpenSearch and Airflow. It includes a patch to disable the `statsd` sidecar which often crashes on Minikube. |
| **6. Search Fix** | `curl -X PUT .../_settings` | **Critical Hack:** Runs a command inside the OpenSearch pod to set replicas to 0 immediately after startup. This fixes "Yellow" cluster status. |
| **7. Core App** | `helm install openmetadata` | Deploys the main server with the high-memory (4GB) profile. |

---

## 📚 Reference Links

* **OpenMetadata Docs:**
    * [Kubernetes Deployment Guide](https://docs.open-metadata.org/deployment/kubernetes)
    * [Helm Charts Repository](https://github.com/open-metadata/openmetadata-helm-charts)
* **Kubernetes Concepts:**
    * [Understanding OOMKilled (Out of Memory)](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/#oom-killer-process)
    * [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
    * [Port Forwarding](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/)
* **Troubleshooting:**
    * [Minikube Memory Limits](https://minikube.sigs.k8s.io/docs/handbook/config/#memory)

## 🐛 Common Issues & Fixes

**Issue: Pods stuck in `CrashLoopBackOff`**
* **Cause:** Usually memory starvation.
* **Fix:** Ensure Minikube was started with at least 12GB RAM (`minikube start --memory=12288`).

**Issue: `Connection Refused` in UI**
* **Cause:** OpenSearch is restarting or not ready.
* **Fix:** Check OpenSearch logs: `kubectl logs -f opensearch-0`. Wait for the "Cluster is Yellow" message.

**Issue: `context deadline exceeded` during install**
* **Cause:** Docker image pulling is too slow.
* **Fix:** Run the `minikube image load` commands manually before the script to cache the images.

```

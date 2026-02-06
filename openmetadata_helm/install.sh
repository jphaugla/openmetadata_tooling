#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Add Helm Repos
helm repo add open-metadata https://helm.open-metadata.org
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 1. Cleanup
echo "Cleaning up previous installations..."
# Delete the releases first so pods release their hold on the volumes
helm uninstall openmetadata openmetadata-dependencies openmetadata-postgres 2>/dev/null

# Wait for pods to actually terminate (important!)
echo "Waiting for pods to terminate..."
kubectl wait --for=delete pod --all --timeout=60s 2>/dev/null

# Now delete the PVCs, with a fallback to force-delete if they get stuck
echo "Deleting volumes..."
kubectl delete pvc --all --timeout=10s 2>/dev/null
if [ $? -ne 0 ]; then
  echo "PVCs stuck in Terminating state. Force patching finalizers..."
  kubectl get pvc --no-headers | awk '{print $1}' | xargs -I {} kubectl patch pvc {} -p '{"metadata":{"finalizers": null}}' 2>/dev/null
fi

kubectl delete jobs --all 2>/dev/null
rm -f "$DIR/deps.yaml"

# 2. Create Secrets
echo "Creating secrets..."
kubectl create secret generic postgresql-secrets \
  --from-literal=openmetadata-postgresql-password=password \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic airflow-secrets \
  --from-literal=openmetadata-airflow-password=admin \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Pre-load Images (Optional)
echo "Pre-loading official images..."
minikube image load docker.getcollate.io/openmetadata/postgresql:1.11.6 2>/dev/null
minikube image load docker.getcollate.io/openmetadata/ingestion:1.11.6 2>/dev/null
minikube image load docker.getcollate.io/openmetadata/server:1.11.6 2>/dev/null

# 4. Install Standalone PostgreSQL
echo "Installing PostgreSQL..."
helm upgrade --install openmetadata-postgres bitnami/postgresql \
  -f "$DIR/postgres-values.yaml" \
  --set global.security.allowInsecureImages=true \
  --set image.registry=docker.getcollate.io \
  --set image.repository=openmetadata/postgresql \
  --set image.tag=1.11.6 \
  --set global.postgresql.auth.postgresPassword=password \
  --set primary.initdb.scripts."init\.sql"="CREATE DATABASE openmetadata_db; CREATE DATABASE airflow_db;" \
  --set primary.persistence.enabled=false \
  --set fullnameOverride=openmetadata-postgres

echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql --timeout=180s

# 5. Create Config for Dependencies (OpenSearch Memory + Probes)
echo "Generating dependency config..."
cat <<EOF > "$DIR/deps.yaml"
# Turn off StatsD to prevent that crash loop you saw
global:
  statsd:
    enabled: false

mysql:
  enabled: false
airflow:
  postgresql:
    enabled: false
  data:
    metadataConnection:
      protocol: postgresql
      host: openmetadata-postgres
      port: 5432
      db: airflow_db
      user: postgres
      pass: password
  images:
    airflow:
      repository: docker.getcollate.io/openmetadata/ingestion
      tag: 1.11.6
opensearch:
  fullnameOverride: "opensearch"
  replicas: 1
  singleNode: true
  
  # INCREASED MEMORY TO PREVENT CRASHLOOPBACKOFF
  resources:
    requests:
      memory: "1024Mi"
      cpu: "500m"
    limits:
      memory: "2560Mi"
      cpu: "2000m"

  # INCREASED TIMEOUTS FOR MINIKUBE
  startupProbe:
    tcpSocket:
      port: 9200
    initialDelaySeconds: 200
    periodSeconds: 30
    failureThreshold: 30
  livenessProbe:
    tcpSocket:
      port: 9200
    initialDelaySeconds: 200
    periodSeconds: 30
    failureThreshold: 10
  readinessProbe:
    tcpSocket:
      port: 9200
    initialDelaySeconds: 200
    periodSeconds: 30
    failureThreshold: 10
    
  # Config with Security Disabled
  config:
    opensearch.yml: |
      cluster.name: opensearch
      node.name: opensearch-0
      discovery.type: single-node
      plugins.security.disabled: true
      bootstrap.memory_lock: false
      cluster.routing.allocation.disk.threshold_enabled: false
EOF

# 6. Install Dependencies using the new file
echo "Installing OpenMetadata dependencies..."
helm upgrade --install openmetadata-dependencies open-metadata/openmetadata-dependencies \
  -f "$DIR/deps.yaml"

# 7. Critical Wait Step
echo "Waiting for OpenSearch to be healthy..."
sleep 30
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=opensearch --timeout=300s

# 7.5. Runtime Fix for Replicas
echo "Applying replica fix to OpenSearch..."
kubectl exec -it opensearch-0 -- curl -X PUT "http://localhost:9200/_all/_settings" \
  -H 'Content-Type: application/json' \
  -d '{"index.number_of_replicas": 0}' 2>/dev/null || echo "Replica fix warning (non-fatal)"

# 8. Install OpenMetadata Core (With 4GB Memory Fix)
echo "Installing OpenMetadata core..."
helm upgrade --install openmetadata open-metadata/openmetadata \
  -f "$DIR/values.yaml" \
  --set resources.requests.memory="2048Mi" \
  --set resources.limits.memory="4096Mi" \
  --set resources.requests.cpu="1000m" \
  --set resources.limits.cpu="2000m" \
  --set livenessProbe.initialDelaySeconds=180 \
  --set readinessProbe.initialDelaySeconds=180 \
  --wait --rollback-on-failure --timeout 10m0s

echo "Installation complete. Checking pod status..."
kubectl get pods

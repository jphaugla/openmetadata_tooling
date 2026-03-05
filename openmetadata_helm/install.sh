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

# 3. Pre-load Images (Optional)
echo "Pre-loading official images..."
minikube image load docker.getcollate.io/openmetadata/postgresql:1.12.1 2>/dev/null
minikube image load docker.getcollate.io/openmetadata/ingestion:1.12.1 2>/dev/null
minikube image load docker.getcollate.io/openmetadata/ingestion-base:1.12.1 2>/dev/null
minikube image load docker.getcollate.io/openmetadata/server:1.12.1 2>/dev/null

# 4. Install Standalone PostgreSQL
echo "Installing PostgreSQL..."
helm upgrade --install openmetadata-postgres bitnami/postgresql \
  -f "$DIR/postgres-values.yaml" \
  --set global.security.allowInsecureImages=true \
  --set image.registry=docker.getcollate.io \
  --set image.repository=openmetadata/postgresql \
  --set image.tag=1.12.1 \
  --set global.postgresql.auth.postgresPassword=password \
  --set primary.initdb.scripts."init\.sql"="CREATE DATABASE openmetadata_db;" \
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
  enabled: false
opensearch:
  fullnameOverride: "opensearch"
  replicas: 1
  singleNode: true
  
  persistence:
    enabled: false
  
  # INCREASED MEMORY TO PREVENT CRASHLOOPBACKOFF
  resources:
    requests:
      memory: "1024Mi"
      cpu: "500m"
    limits:
      memory: "2048Mi"
      cpu: "1000m"

  # FASTER PROBES FOR RAM DISK
  startupProbe:
    tcpSocket:
      port: 9200
    initialDelaySeconds: 10
    periodSeconds: 10
    failureThreshold: 30
  livenessProbe:
    tcpSocket:
      port: 9200
    initialDelaySeconds: 30
    periodSeconds: 10
    failureThreshold: 10
  readinessProbe:
    tcpSocket:
      port: 9200
    initialDelaySeconds: 30
    periodSeconds: 10
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
echo "Waiting for OpenSearch API to be responsive..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=opensearch --timeout=300s

# Now wait for the actual API to return a healthy cluster status
MAX_RETRIES=20
COUNT=0
until kubectl exec opensearch-0 -- curl -s "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=5s" >/dev/null 2>&1; do
  echo "OpenSearch cluster manager not discovered yet (attempt $((++COUNT))/$MAX_RETRIES)..."
  if [ $COUNT -ge $MAX_RETRIES ]; then
    echo "❌ Timeout waiting for OpenSearch API."
    exit 1
  fi
  sleep 5
done
echo "✅ OpenSearch API is healthy."

# 7.5. Runtime Fix for Replicas
echo "Applying replica fix to OpenSearch..."
for i in {1..5}; do
  RESPONSE=$(kubectl exec opensearch-0 -- curl -s -X PUT "http://localhost:9200/_all/_settings" \
    -H 'Content-Type: application/json' \
    -d '{"index.number_of_replicas": 0}')
  if echo "$RESPONSE" | grep -q "acknowledged"; then
    echo "✅ Replicas set to 0."
    break
  fi
  echo "⚠️ Replica fix failed, retrying in 5s... ($RESPONSE)"
  sleep 5
done

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
  --wait --timeout 30m0s

echo "Installation complete. Checking pod status..."
kubectl get pods

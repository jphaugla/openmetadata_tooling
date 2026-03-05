#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "🆙 Upgrading OpenMetadata Core with new configuration..."

helm upgrade --install openmetadata open-metadata/openmetadata \
  -f "$DIR/values.yaml" \
  --set resources.requests.memory="2048Mi" \
  --set resources.limits.memory="4096Mi" \
  --set resources.requests.cpu="1000m" \
  --set resources.limits.cpu="2000m" \
  --set livenessProbe.initialDelaySeconds=180 \
  --set readinessProbe.initialDelaySeconds=180 \
  --wait --timeout 30m0s

echo "🔄 Forcing pod restart to apply new configuration..."
kubectl rollout restart deployment openmetadata
kubectl rollout status deployment openmetadata

echo "✅ Upgrade and Rollout complete."
kubectl get pods

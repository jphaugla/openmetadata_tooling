#!/bin/bash

# Cassandra Connectivity Test from Hybrid Runner
# This script tests if the OrbStack Hybrid Runner can reach your Mac's Cassandra instance.

NAMESPACE="collate-runner"
HOST="host.orb.internal"
PORT="9042"

echo "🔍 Searching for the Hybrid Runner pod in namespace: $NAMESPACE..."

# Find the active runner pod
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=hybrid-ingestion-runner -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    # Fallback to a broader search if the label differs
    POD_NAME=$(kubectl get pods -n $NAMESPACE --no-headers -o custom-columns=":metadata.name" | grep "hybrid-ingestion-runner" | head -n 1)
fi

if [ -z "$POD_NAME" ]; then
    echo "❌ Error: Could not find a running Hybrid Runner pod."
    echo "Please check if it's running with: kubectl get pods -n $NAMESPACE"
    exit 1
fi

echo "✅ Found pod: $POD_NAME"
echo "⏳ Testing connection to $HOST:$PORT..."

# Execute the test inside the pod
kubectl exec -n $NAMESPACE $POD_NAME -- bash -c "timeout 2 bash -c \"</dev/tcp/$HOST/$PORT\"" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "🎉 SUCCESS: The Hybrid Runner can reach your local Cassandra!"
else
    echo "❌ FAILURE: Connection timed out or refused."
    echo "Check if Cassandra is running and rpc_address is set to 0.0.0.0 in cassandra.yaml"
fi

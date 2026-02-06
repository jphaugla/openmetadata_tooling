export PORT=26257
# Validate CERTS_DIR
if [ -z "$CERTS_DIR" ]; then
    echo "Error: Missing CERTS_DIR environment variable"
    exit 1
fi
echo 'PORT is ' ${PORT}
cockroach sql --certs-dir=${CERTS_DIR} --host=localhost:${PORT}

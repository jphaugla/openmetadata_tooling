export PORT=26257
export SQL_FILE=$1
# Validate CERTS_DIR
if [ -z "$CERTS_DIR" ] || [ -z "$SQL_FILE" ]; then
    echo "Error: Missing CERTS_DIR environment variable"
    exit 1
fi
echo 'PORT is ' ${PORT}
echo 'SQL_FILE is ' ${SQL_FILE}
cockroach sql --certs-dir=${CERTS_DIR} --host=localhost:${PORT} --file=${SQL_FILE}

#!/bin/bash

# Cassandra Demo Setup Script

echo "🚀 Starting Cassandra Demo Setup..."

# Function to check if Cassandra is running
is_cassandra_running() {
    cqlsh -e "DESCRIBE KEYSPACES" > /dev/null 2>&1
    return $?
}

# Check if Cassandra is running, if not start it
if is_cassandra_running; then
    echo "✅ Cassandra is already running."
else
    echo "⏳ Cassandra is not running. Starting it via brew..."
    brew services start cassandra
    
    # Wait for Cassandra to be ready
    echo "⏳ Waiting for Cassandra to initialize (this may take a minute)..."
    MAX_RETRIES=60
    COUNT=0
    until is_cassandra_running || [ $COUNT -eq $MAX_RETRIES ]; do
        sleep 2
        COUNT=$((COUNT + 1))
        printf "."
    done
    echo ""

    if [ $COUNT -eq $MAX_RETRIES ]; then
        echo "❌ Cassandra failed to start in time. Please check 'brew services list' and logs."
        exit 1
    fi
    echo "✅ Cassandra is ready!"
fi

echo "📂 Creating schema..."
cqlsh -f schema.cql

if [ $? -eq 0 ]; then
    echo "✅ Schema created successfully."
else
    echo "❌ Failed to create schema."
    exit 1
fi

echo "📊 Loading sample data (this might take a moment)..."
cqlsh -f insert_data.cql

if [ $? -eq 0 ]; then
    echo "✅ Sample data loaded successfully."
else
    echo "❌ Failed to load sample data."
    exit 1
fi

echo ""
echo "🎉 Cassandra Demo Environment is ready!"
echo "Keyspace: ecommerce_demo"
echo "Tables: users, products, orders_by_user, inventory_log"
echo ""
echo "You can now connect using: cqlsh -k ecommerce_demo"
echo "Try running: SELECT count(*) FROM users;"

#!/bin/bash
# cleanup.sh

echo "🧹 Cleaning up Cassandra Demo..."

cqlsh -e "DROP KEYSPACE IF EXISTS ecommerce_demo;"

if [ $? -eq 0 ]; then
    echo "✅ Keyspace ecommerce_demo dropped successfully."
else
    echo "❌ Failed to drop keyspace."
fi

# Optional: Stop Cassandra
# echo "🛑 Stopping Cassandra..."
# brew services stop cassandra

#!/bin/bash
# Simple health check to ensure UI and API match

USER_COUNT_DB=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/users" | jq '.paging.total')
USER_COUNT_ES=$(curl -s "http://localhost:9200/user_search_index/_count" | jq '.count')

echo "📊 Database Users: $USER_COUNT_DB"
echo "🔍 Search Index Users: $USER_COUNT_ES"

if [ "$USER_COUNT_DB" -eq "$USER_COUNT_ES" ]; then
    echo "✅ System is in sync!"
else
    echo "⚠️ Mismatch detected. Run ./reindex.sh"
fi

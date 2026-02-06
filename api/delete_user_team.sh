#!/bin/bash

# 1. Get IDs
USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/users/name/jason.haugland" | jq -r .id)
TEAM_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/teams/name/Solution Architects" | jq -r .id)

# 2. Hard Delete User
echo "🗑 Deleting User..."
curl -X DELETE "$API_BASE/users/$USER_ID?hardDelete=true&recursive=true" -H "Authorization: Bearer $TOKEN"

# 3. Hard Delete Team (If it's the one you created)
echo "🗑 Deleting Team..."
curl -X DELETE "$API_BASE/teams/$TEAM_ID?hardDelete=true&recursive=true" -H "Authorization: Bearer $TOKEN"

echo -e "\n✅ Ghost entities purged."

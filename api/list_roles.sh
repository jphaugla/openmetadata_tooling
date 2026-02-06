# List roles to find the Admin UUID
curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/roles" | jq '.data[] | {name: .name, id: .id}'

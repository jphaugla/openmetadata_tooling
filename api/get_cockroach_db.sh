export SERVICE_NAME=Cockroach_intro
curl -X GET "$API_BASE/services/databaseServices/name/${SERVICE_NAME}?fields=connection" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" | python3 -m json.tool > Cockroach_intro.json

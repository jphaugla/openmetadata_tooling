from om_client import OpenMetadataClient
import json
import requests
c = OpenMetadataClient()
s = c._make_request('GET', '/services/databaseServices/name/Enterprise_SE?fields=connection').json()
with open('/tmp/om_creds.json', 'r') as f:
    creds = json.load(f)

config = s['connection']['config']
config['privateKey'] = creds['privateKey']
config['snowflakePrivatekeyPassphrase'] = creds['pass']
config['username'] = creds['user']
# ensure password is removed if it erroneously exists
if 'password' in config:
    del config['password']

patch=[{'op': 'replace', 'path': '/connection/config', 'value': config}]
headers = c.headers.copy()
headers['Content-Type']='application/json-patch+json'
r = requests.patch(f"{c.api_base}/services/databaseServices/{s['id']}", headers=headers, json=patch)
print("Patch Status:", r.status_code)

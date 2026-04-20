from om_client import OpenMetadataClient
import json
import sys
c = OpenMetadataClient()
s = c._make_request('GET', '/services/databaseServices/name/Re Imagine Collate?fields=connection').json()
cfg = s['connection']['config']
with open('/tmp/om_creds.json', 'w') as f:
    json.dump({"privateKey": cfg.get('privateKey'), "pass": cfg.get('snowflakePrivatekeyPassphrase'), "user": cfg.get('username')}, f)

#!/usr/bin/env python3
import json
import base64
import urllib.request
import urllib.error

with open('projeto-migracao/.secrets/loja.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            globals()[k] = v

base = PM_LOJA_URL.rstrip('/')
auth = base64.b64encode(f'{PM_LOJA_USER}:{PM_LOJA_APP_PASSWORD}'.encode()).decode()

# Just check the key range 24248-24272
for pid in range(24248, 24273):
    url = f'{base}/wp-json/wc/v3/products/{pid}'
    req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}', 'User-Agent': 'pm-validate'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
            name = data.get("name", "?")
            ptype = data.get("type", "?")
            price = data.get("price", "?")
            status = data.get("status", "?")
            print(f'{pid}: EXISTS - name={name[:50]} type={ptype} price={price} status={status}')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f'{pid}: NOT FOUND')
        else:
            print(f'{pid}: ERROR {e.code}')
    except Exception as e:
        print(f'{pid}: EXCEPTION - {e}')
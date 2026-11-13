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

# Check old shared IDs and new IDs
ids_to_check = [9863, 4213, 24248, 24249, 24250, 24251, 24252, 24253, 24254, 24255]

for pid in ids_to_check:
    url = f'{base}/wp-json/wc/v3/products/{pid}'
    req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}', 'User-Agent': 'pm-validate'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
            name = data.get('name', '?')
            ptype = data.get('type', '?')
            price = data.get('price', '?')
            status = data.get('status', '?')
            print(f'{pid}: EXISTS - name={name[:60]} type={ptype} price={price} status={status}')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f'{pid}: NOT FOUND')
        else:
            print(f'{pid}: ERROR {e.code}')
    except Exception as e:
        print(f'{pid}: EXCEPTION - {e}')

# Also search for virilha laser products
print("\n=== SEARCH: virilha ===")
url = f'{base}/wp-json/wc/v3/products?search=virilha&per_page=100'
req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}', 'User-Agent': 'pm-validate'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
        for prod in data:
            name = prod.get('name', '')
            ptype = prod.get('type', '')
            price = prod.get('price', '')
            status = prod.get('status', '')
            print(f'ID={prod.get("id")}: name={name[:60]} type={ptype} price={price} status={status}')
except Exception as e:
    print(f'ERROR: {e}')
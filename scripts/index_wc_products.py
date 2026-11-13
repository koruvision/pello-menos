#!/usr/bin/env python3
"""Fetch all WooCommerce products and build an index by name and slug."""
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

all_products = []
page = 1
while True:
    url = f'{base}/wp-json/wc/v3/products?per_page=100&page={page}'
    req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}', 'User-Agent': 'pm-validate'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
            if not data:
                break
            all_products.extend(data)
            if len(data) < 100:
                break
            page += 1
    except urllib.error.HTTPError as e:
        print(f'HTTP error on page {page}: {e.code}')
        break
    except Exception as e:
        print(f'Exception on page {page}: {e}')
        break

print(f'Total products fetched: {len(all_products)}')

# Build index
by_id = {}
by_name = {}
for p in all_products:
    pid = p.get('id')
    name = p.get('name', '')
    ptype = p.get('type', '')
    price = p.get('price', '')
    status = p.get('status', '')
    by_id[pid] = {'name': name, 'type': ptype, 'price': price, 'status': status}
    by_name[name.lower().strip()] = pid

# Save index
with open('scripts/_wc_index.json', 'w', encoding='utf-8') as f:
    json.dump({'by_id': {str(k): v for k, v in by_id.items()}, 'by_name': by_name}, f, ensure_ascii=False, indent=2)

print(f'Index saved: {len(by_id)} products, {len(by_name)} names')

# Print all products sorted by name for review
print('\n=== ALL PRODUCTS (sorted by name) ===')
for pid in sorted(by_id.keys(), key=lambda x: by_id[x]['name'].lower()):
    info = by_id[pid]
    print(f'ID={pid}: name={info["name"][:60]} type={info["type"]} price={info["price"]} status={info["status"]}')
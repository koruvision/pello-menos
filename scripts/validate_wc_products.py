#!/usr/bin/env python3
"""Validate that all bridge productIds exist in WooCommerce."""
import json
import base64
import urllib.request
import urllib.error
import time

# Load credentials
with open('projeto-migracao/.secrets/loja.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            globals()[k] = v

base = PM_LOJA_URL.rstrip('/')
auth = base64.b64encode(f'{PM_LOJA_USER}:{PM_LOJA_APP_PASSWORD}'.encode()).decode()

# Extract all unique productIds from local bridge
with open('src/lib/woo-bridge.json', encoding='utf-8') as f:
    bridge = json.load(f)

all_ids = set()
for k, v in bridge.items():
    if v.get('productId'):
        all_ids.add(v['productId'])
    units = v.get('units') or {}
    for uid, meta in units.items():
        if meta.get('variationId'):
            all_ids.add(meta['variationId'])

print(f"Total unique productIds/variationIds to check: {len(all_ids)}")

# Check each ID
not_found = []
errors = []
start = time.time()
for i, pid in enumerate(sorted(all_ids), 1):
    url = f'{base}/wp-json/wc/v3/products/{pid}'
    req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}', 'User-Agent': 'pm-validate'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
            if i % 50 == 0:
                elapsed = time.time() - start
                print(f"  [{i}/{len(all_ids)}] {pid}: OK - {data.get('name')[:40]}... ({elapsed:.1f}s)")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            not_found.append(pid)
            print(f"  [{i}/{len(all_ids)}] {pid}: NOT FOUND (404)")
        else:
            errors.append((pid, e.code, e.read()[:200]))
            print(f"  [{i}/{len(all_ids)}] {pid}: ERROR {e.code}")
    except Exception as e:
        errors.append((pid, 0, str(e)))
        print(f"  [{i}/{len(all_ids)}] {pid}: EXCEPTION - {e}")

elapsed = time.time() - start
print(f"\n=== SUMMARY ({elapsed:.1f}s) ===")
print(f"Total checked: {len(all_ids)}")
print(f"Not found (404): {len(not_found)}")
print(f"Errors: {len(errors)}")
if not_found:
    print(f"\nMISSING IDs ({len(not_found)}): {sorted(not_found)}")
if errors:
    print(f"\nERROR IDs:")
    for pid, code, msg in errors[:20]:
        print(f"  {pid}: code={code} msg={msg}")

# Also specifically check the 24248-24272 range
print("\n=== KEY RANGE 24248-24272 ===")
for pid in range(24248, 24273):
    url = f'{base}/wp-json/wc/v3/products/{pid}'
    req = urllib.request.Request(url, headers={'Authorization': f'Basic {auth}', 'User-Agent': 'pm-validate'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
            print(f"  {pid}: EXISTS - name={data.get('name')} type={data.get('type')} price={data.get('price')} status={data.get('status')}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  {pid}: NOT FOUND")
        else:
            print(f"  {pid}: ERROR {e.code}")
    except Exception as e:
        print(f"  {pid}: EXCEPTION - {e}")
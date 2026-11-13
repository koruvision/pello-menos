import base64,json,urllib.request
from pathlib import Path
e={}
for line in Path("projeto-migracao/.secrets/loja.env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k,v=line.split("=",1); e[k.strip().lstrip("\ufeff")]=v.strip()
auth=base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
base=e["PM_LOJA_URL"].rstrip("/")
def get(path):
    req=urllib.request.Request(base+path,headers={"Authorization":"Basic "+auth,"Accept":"application/json","User-Agent":"pm"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode())
for oid in (49488,49541,49500,49525,49524):
    o=get(f"/wp-json/wc/v3/orders/{oid}")
    b=o.get("billing") or {}
    print(oid, o.get("status"), "fn=",repr(b.get("first_name")), "em=",b.get("email"), "st=",repr(b.get("state")))
    cid=o.get("customer_id")
    if cid:
        c=get(f"/wp-json/wc/v3/customers/{cid}")
        print("  cust",cid,"user=",c.get("username"),"first=",repr(c.get("first_name")),"last=",repr(c.get("last_name")))

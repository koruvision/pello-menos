import base64,json,urllib.request,urllib.parse
from pathlib import Path
e={}
for line in Path("projeto-migracao/.secrets/loja.env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k,v=line.split("=",1); e[k.strip().lstrip("\ufeff")]=v.strip()
auth=base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
base=e["PM_LOJA_URL"].rstrip("/")
def get(path):
    req=urllib.request.Request(base+path,headers={"Authorization":"Basic "+auth,"Accept":"application/json","User-Agent":"pm"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return json.loads(r.read().decode()), r.headers
# search customers/orders by email fragments
queries=["neli","mayry","marcela","botelho","elehe","souto","nilopolis"]
# recent orders last 2 days
page=1
hits=[]
while page<=5:
    q=urllib.parse.urlencode({"after":"2026-11-04T00:00:00","per_page":100,"page":page,"orderby":"date","order":"desc","status":"any"})
    rows,h=get("/wp-json/wc/v3/orders?"+q)
    if not rows: break
    for o in rows:
        b=o.get("billing") or {}
        blob=" ".join([str(b.get("first_name") or ""), str(b.get("email") or ""), str(o.get("id"))]).lower()
        meta={m["key"]:m["value"] for m in o.get("meta_data") or [] if m.get("key") in ("Unidade","Pedido Accesstage")}
        if any(x in blob for x in ("neli","mayry","marcela","botelho","elehe","souto")) or meta.get("Unidade") in ("nilopolis","largomachado"):
            if meta.get("Unidade") in ("nilopolis","largomachado") or any(x in blob for x in ("neli","mayry","marcela","botelho","elehe","souto")):
                hits.append((o["id"], o["status"], b.get("first_name"), b.get("email"), meta.get("Unidade"), o.get("total"), o.get("date_created")))
    if page >= int(h.get("X-WP-TotalPages") or 1): break
    page+=1
print("hits", len(hits))
for h in hits[:40]:
    print(h)
# count states not 2 chars among recent completed
bad_state=0
email_name=0
sample_states={}
page=1
while page<=3:
    q=urllib.parse.urlencode({"after":"2026-11-03T00:00:00","per_page":100,"page":page,"status":"completed"})
    rows,h=get("/wp-json/wc/v3/orders?"+q)
    for o in rows:
        st=(o.get("billing") or {}).get("state") or ""
        fn=(o.get("billing") or {}).get("first_name") or ""
        sample_states[st]=sample_states.get(st,0)+1
        if len(st)!=2: bad_state+=1
        if "@" in fn: email_name+=1
    if page >= int(h.get("X-WP-TotalPages") or 1): break
    page+=1
print("bad_state", bad_state, "email_as_name", email_name, "states", sample_states)

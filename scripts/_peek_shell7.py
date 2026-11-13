# -*- coding: utf-8 -*-
import time
import urllib.request

base = "https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/checkout-shell.js"
for q in ("?v=shell7", "?v=shell10", "?nocache=" + str(time.time())):
    t = urllib.request.urlopen(base + q, timeout=120).read().decode("utf-8", "replace")
    print(
        q,
        "len",
        len(t),
        "boot",
        "__pmShellBoot" in t,
        "lock",
        "__pmTotalsLock" in t,
        "sync",
        "syncCheckoutTotalsFromWoo" in t,
    )

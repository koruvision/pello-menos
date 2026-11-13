import time
import urllib.request

url = (
    "https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/checkout-shell.js?nocache="
    + str(time.time())
)
t = urllib.request.urlopen(url, timeout=120).read().decode("utf-8", "replace")
print("empty-cart guard", "Ignore empty-cart" in t or "session hydrates" in t)
print("notify false comment", "Never dispatch change" in t)
print("interval 300", "}, 300);" in t)
# boot marker check
print("has scheduleCheckoutSync call", "scheduleCheckoutSync();" in t)

import urllib.request
import json
import os
import requests

printify_key = os.environ["PRINTIFY_API_KEY"]
printify_shop = os.environ["PRINTIFY_SHOP_ID"]
wix_key = os.environ["WIX_API_KEY"]
wix_site = os.environ["WIX_SITE_ID"]
wix_account = os.environ["WIX_ACCOUNT_ID"]

# Fetch all Printify products (paginated)
import requests

headers = {"Authorization": "Bearer " + printify_key}
url = "https://api.printify.com/v1/shops/" + printify_shop + "/products.json?limit=50&page=1"
r = requests.get(url, headers=headers)
print(r.status_code, r.text[:200])

printify_titles = set()
page = 1
while True:
    url = "https://api.printify.com/v1/shops/" + printify_shop + "/products.json?limit=50&page=" + str(page)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + printify_key})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    products = data.get("data", [])
    for p in products:
        printify_titles.add(p["title"].strip().lower())
    if len(products) < 50:
        break
    page += 1

print(f"Printify products found: {len(printify_titles)}")

# Fetch all Wix products (paginated via cursor)
wix_products = []
cursor = None
while True:
    body = {"limit": 100}
    if cursor:
        body["cursorPaging"] = {"cursor": cursor}
    req = urllib.request.Request(
        "https://www.wixapis.com/stores/v3/products/query",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": wix_key,
            "wix-site-id": wix_site,
            "wix-account-id": wix_account,
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    batch = data.get("products", [])
    wix_products.extend(batch)
    cursor = data.get("pagingMetadata", {}).get("cursors", {}).get("next")
    if not cursor or len(batch) == 0:
        break

print(f"Wix products found: {len(wix_products)}")

# Wix-exclusive products
print("\n--- WIX-EXCLUSIVE PRODUCTS (not in Printify) ---\n")
wix_only = []
for p in wix_products:
    title = p.get("name", "").strip()
    if title.lower() not in printify_titles:
        wix_only.append(title)

for title in sorted(wix_only):
    print(" ", title)

print(f"\nTotal Wix-exclusive: {len(wix_only)}")

# Full Printify list
print("\n--- ALL PRINTIFY PRODUCTS ---\n")
for t in sorted(printify_titles):
    print(" ", t)

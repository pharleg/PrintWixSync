import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Credentials ---
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")
WIX_ACCOUNT_ID = os.getenv("WIX_ACCOUNT_ID")
PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID")

WIX_HEADERS = {
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
    "wix-account-id": WIX_ACCOUNT_ID,
    "Content-Type": "application/json",
}

PRINTIFY_HEADERS = {
    "Authorization": f"Bearer {PRINTIFY_API_KEY}",
    "Content-Type": "application/json",
}


# --- Wix ---

def fetch_wix_products():
    products = []
    cursor = None
    url = "https://www.wixapis.com/stores/v1/products/query"

    while True:
        body = {"query": {"paging": {"limit": 100}}}
        if cursor:
            body["cursorPaging"]["cursor"] = cursor

        resp = requests.post(url, headers=WIX_HEADERS, json=body)
        if not resp.ok:
            print(f"Wix error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        
        batch = data.get("products", [])
        products.extend(batch)

        cursor = data.get("pagingMetadata", {}).get("cursors", {}).get("next")
        if not cursor or not batch:
            break

    return products


# --- Printify ---

def fetch_printify_products():
    products = []
    page = 1

    while True:
        url = f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products.json?page={page}&limit=100"
        resp = requests.get(url, headers=PRINTIFY_HEADERS)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("data", [])
        products.extend(batch)

        if page >= data.get("last_page", 1):
            break
        page += 1

    return products


# --- Match ---

def match_products(wix_products, printify_products):
    printify_titles = {p["title"].strip().lower(): p for p in printify_products}

    matched = []
    wix_only = []

    for wp in wix_products:
        title = wp.get("name", "").strip().lower()
        if title in printify_titles:
            matched.append({
                "title": wp.get("name"),
                "wix_id": wp.get("id"),
                "printify_id": printify_titles[title]["id"],
                "source": "printify",
                "wix_description": wp.get("description", ""),
                "printify_description": printify_titles[title].get("description", ""),
            })
        else:
            wix_only.append({
                "title": wp.get("name"),
                "wix_id": wp.get("id"),
                "source": "wix",
                "description": wp.get("description", ""),
            })

    return matched, wix_only


# --- Main ---

if __name__ == "__main__":
    print("Fetching Wix products...")
    wix_products = fetch_wix_products()
    print(f"  Found {len(wix_products)} Wix products")

    print("Fetching Printify products...")
    printify_products = fetch_printify_products()
    print(f"  Found {len(printify_products)} Printify products")

    print("Matching...")
    matched, wix_only = match_products(wix_products, printify_products)

    print(f"\nResults:")
    print(f"  Printify-sourced: {len(matched)}")
    print(f"  Wix-native: {len(wix_only)}")

    output = {
        "printify_products": matched,
        "wix_native_products": wix_only,
    }

    with open("products.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\nSaved to products.json")

import os
import re
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
    url = "https://www.wixapis.com/stores/v3/products/query"

    while True:
        body = {"cursorPaging": {"limit": 100}}
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
        url = f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products.json?page={page}&limit=50"
        resp = requests.get(url, headers=PRINTIFY_HEADERS)
        if not resp.ok:
            print(f"Printify error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("data", [])
        products.extend(batch)

        if page >= data.get("last_page", 1):
            break
        page += 1

    return products


# --- Matching ---

def normalize(title):
    title = title.lower()
    title = re.sub(r'[^a-z0-9 ]', ' ', title)
    for filler in [" the ", " a ", " an ", " and ", " or ", " with ", " for ", " in ", " of "]:
        title = title.replace(filler, " ")
    return re.sub(r'\s+', ' ', title).strip()


def fuzzy_score(wix_title, printify_title):
    wix_words = set(normalize(wix_title).split())
    p_words = set(normalize(printify_title).split())
    overlap = len(wix_words & p_words)
    return overlap / max(len(wix_words), len(p_words))


def match_products(wix_products, printify_products):
    matched = []
    wix_only = []
    duplicates = []

    for wp in wix_products:
        wix_title = wp.get("name", "")

        best_score = 0
        best_pp = None

        for pp in printify_products:
            score = fuzzy_score(wix_title, pp["title"])
            if score > best_score:
                best_score = score
                best_pp = pp

        if best_score == 1.0:
            matched.append({
                "title": wix_title,
                "match_type": "exact",
                "wix_id": wp.get("id"),
                "printify_id": best_pp["id"],
                "source": "printify",
                "wix_description": wp.get("description", ""),
                "printify_description": best_pp.get("description", ""),
            })
        elif best_score >= 0.4:
            duplicates.append({
                "wix_title": wix_title,
                "printify_title": best_pp["title"],
                "match_score": round(best_score, 2),
                "wix_id": wp.get("id"),
                "printify_id": best_pp["id"],
                "action": "review: remove from Wix if confirmed same product, sync from Printify",
            })
        else:
            wix_only.append({
                "title": wix_title,
                "wix_id": wp.get("id"),
                "source": "wix",
                "description": wp.get("description", ""),
            })

    return matched, wix_only, duplicates


# --- Main ---

if __name__ == "__main__":
    print("Fetching Wix products...")
    wix_products = fetch_wix_products()
    print(f"  Found {len(wix_products)} Wix products")

    print("Fetching Printify products...")
    printify_products = fetch_printify_products()
    print(f"  Found {len(printify_products)} Printify products")

    print("Matching...")
    matched, wix_only, duplicates = match_products(wix_products, printify_products)

    print(f"\nResults:")
    print(f"  Confirmed Printify-sourced: {len(matched)}")
    print(f"  Possible duplicates (review needed): {len(duplicates)}")
    print(f"  Wix-native: {len(wix_only)}")

    if duplicates:
        print(f"\nPossible duplicates:")
        for d in duplicates:
            print(f"  [{d['match_score']}] Wix: \"{d['wix_title']}\"")
            print(f"        Printify: \"{d['printify_title']}\"")

    output = {
        "printify_products": matched,
        "possible_duplicates": duplicates,
        "wix_native_products": wix_only,
    }

    with open("products.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\nSaved to products.json")

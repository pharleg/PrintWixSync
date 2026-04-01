# PrintWixSync

Pulls products from both Printify and Wix, matches them by title, and identifies which products are Printify-sourced vs Wix-native. Used as the foundation for bulk description updates routed to the correct API.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in .env with your credentials
```

## Usage

### Pull and match all products
```bash
python sync.py
```

Outputs `products.json` with two arrays:
- `printify_products` -- matched to a Printify source, update via Printify API
- `wix_native_products` -- Wix-only, update via Wix Catalog V3 API

## Credentials needed

| Variable | Where to find it |
|---|---|
| WIX_API_KEY | Wix Dev Center > API Keys |
| WIX_SITE_ID | Wix Dev Center > Your Site |
| WIX_ACCOUNT_ID | Wix Dev Center > Your Account |
| PRINTIFY_API_KEY | Printify > My Profile > Connections |
| PRINTIFY_SHOP_ID | Printify API > GET /v1/shops.json |

import requests
import json
from datetime import datetime

API_TOKEN = "c256294fdf640a640e44ac44dc6f41f281a8c2a5864d87d77135818c1f18292a"

cik_list = [
    {"cik": "0001067983", "name": "Berkshire Hathaway"},
    {"cik": "0001066768", "name": "Renaissance Technologies"},
    {"cik": "0001083306", "name": "Bridgewater Associates"},
    {"cik": "0001571317", "name": "ARK Invest"},
    {"cik": "0001382118", "name": "Tiger Global"}
]

holdings = {}

for item in cik_list:
    cik = item["cik"]
    name = item["name"]
    url = f"https://api.sec-api.io/filings/13f?cik={cik}&date=latest&token={API_TOKEN}"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            print(f"Error fetching {name}: HTTP {resp.status_code}")
            continue
        data = resp.json()
        if not data or "holdings" not in data:
            continue
        for holding in data.get("holdings", []):
            ticker = holding.get("ticker")
            if not ticker:
                continue
            value = holding.get("value", 0) / 1000
            if ticker not in holdings:
                holdings[ticker] = {}
            holdings[ticker][name] = holdings[ticker].get(name, 0) + value
    except Exception as e:
        print(f"Exception for {name}: {e}")

output = {
    "latest": {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "holdings": holdings
    },
    "previous": {}
}

with open("13f_latest.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Saved {len(holdings)} symbols")

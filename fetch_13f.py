import json
import os
import sys
from datetime import datetime

import requests

# 金鑰只從環境變數讀（GitHub Secrets: SEC_API_TOKEN），不寫進程式碼
API_TOKEN = os.environ.get("SEC_API_TOKEN", "").strip()
OUT_FILE = "13f_latest.json"

cik_list = [
    {"cik": "0001067983", "name": "Berkshire Hathaway"},
    {"cik": "0001066768", "name": "Renaissance Technologies"},
    {"cik": "0001083306", "name": "Bridgewater Associates"},
    {"cik": "0001571317", "name": "ARK Invest"},
    {"cik": "0001382118", "name": "Tiger Global"},
]


def main():
    if not API_TOKEN:
        print("ERROR: SEC_API_TOKEN 未設定")
        return 1

    holdings = {}
    failed = []
    for item in cik_list:
        cik, name = item["cik"], item["name"]
        url = f"https://api.sec-api.io/filings/13f?cik={cik}&date=latest&token={API_TOKEN}"
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                print(f"Error fetching {name}: HTTP {resp.status_code}")
                failed.append(name)
                continue
            data = resp.json()
            if not data or "holdings" not in data:
                print(f"No holdings for {name}")
                failed.append(name)
                continue
            for h in data.get("holdings", []):
                ticker = h.get("ticker")
                if not ticker:
                    continue
                value = (h.get("value", 0) or 0) / 1000
                holdings.setdefault(ticker, {})
                holdings[ticker][name] = holdings[ticker].get(name, 0) + value
        except Exception as e:
            print(f"Exception for {name}: {type(e).__name__}")
            failed.append(name)

    # 任何一家失敗就不覆蓋，避免殘缺資料被當完整季報
    if failed or not holdings:
        print(f"ABORT: 失敗={failed} 標的數={len(holdings)}，不更新檔案")
        return 1

    old = {}
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, encoding="utf-8") as f:
                old = json.load(f)
        except Exception:
            old = {}
    old_latest = old.get("latest") or {}
    old_prev = old.get("previous") or {}

    if old_latest.get("holdings") == holdings:
        print("持股與上次相同（13F 每季才更新），不改檔")
        return 0

    # 持股有變 = 新一季：舊 latest 變 previous，主程式才算得出買賣差
    previous = old_latest if old_latest.get("holdings") else old_prev
    output = {
        "latest": {"date": datetime.now().strftime("%Y-%m-%d"), "holdings": holdings},
        "previous": previous,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(holdings)} symbols, previous={'有' if previous else '無'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

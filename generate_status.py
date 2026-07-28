import concurrent.futures
import json
from datetime import datetime
import requests

SERVICES = {
    "Epic Games": {
        "url": "https://status.epicgames.com/api/v2/summary.json",
        "type": "statuspage",
    },
    "Steam": {"url": "https://steamstat.us/status.json", "type": "steamstatus"},
    "PlayStation Network": {
        "url": "https://status.playstation.com/en-US/",
        "type": "http_check",
    },
    "Xbox Live": {
        "url": "https://support.xbox.com/en-US/xbox-live-status",
        "type": "http_check",
    },
    "EA Services": {
        "url": "https://help.ea.com/en/server-status/",
        "type": "http_check",
    },
    "Nintendo Network": {
        "url": "https://www.nintendo.co.jp/netinfo/en_US/index.html",
        "type": "http_check",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def check_service(name, config):
    url = config["url"]
    check_type = config["type"]
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if check_type == "statuspage":
            data = res.json()
            indicator = data.get("status", {}).get("indicator", "none")
            is_ok = indicator in ["none", "minor"]
            return {
                "name": name,
                "ok": is_ok,
                "status": "Operational" if is_ok else "Issues Detected",
            }
        elif check_type == "steamstatus":
            is_ok = res.status_code == 200
            return {
                "name": name,
                "ok": is_ok,
                "status": "Operational" if is_ok else "Degraded",
            }
        else:
            is_ok = res.status_code == 200
            return {
                "name": name,
                "ok": is_ok,
                "status": "Reachable" if is_ok else f"HTTP {res.status_code}",
            }
    except Exception as e:
        return {
            "name": name,
            "ok": False,
            "status": f"Unreachable ({type(e).__name__})",
        }


def main():
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(check_service, name, cfg)
            for name, cfg in SERVICES.items()
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # مرتب‌سازی بر اساس نام
    results.sort(key=lambda x: x["name"])
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # ذخیره فایل JSON (برای استفاده‌های بعدی مثل ربات یا API)
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"updated_at": now, "services": results}, f, indent=2)

    # ساخت فایل HTML دشبورد
    cards_html = ""
    for s in results:
        badge_cls = "bg-green" if s["ok"] else "bg-red"
        badge_text = s["status"]
        cards_html += f"""
        <div class="card">
            <span class="name">{s['name']}</span>
            <span class="badge {badge_cls}">{badge_text}</span>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60">
    <title>Game Services Status</title>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 500px; }}
        h2 {{ text-align: center; color: #38bdf8; }}
        .updated {{ font-size: 0.8rem; color: #94a3b8; text-align: center; margin-bottom: 20px; }}
        .card {{ background: #1e293b; padding: 15px 20px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #334155; }}
        .name {{ font-weight: bold; }}
        .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: bold; }}
        .bg-green {{ background: #059669; color: #fff; }}
        .bg-red {{ background: #dc2626; color: #fff; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>🎮 وضعیت سرویس‌های گیمینگ</h2>
        <div class="updated">آخرین بروزرسانی: {now}</div>
        {cards_html}
    </div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    main()

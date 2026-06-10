#!/usr/bin/env python3
"""
Daily Debrief — main orchestrator.
Runs all active modules, passes results to the HTML builder.
Add a new module by dropping a file in /modules and registering it below.
"""

import os, json, importlib, traceback
from datetime import datetime
from builder import build_dashboard

# ── Register modules here ───────────────────────────────────────
# Each entry: { "id": str, "label": str, "icon": str, "module": str }
# Set enabled=False to skip without deleting the module.
MODULES = [
    {"id": "email",    "label": "Inbox",        "icon": "mail-bolt",      "module": "modules.email_module",    "enabled": True},
    {"id": "stocks",   "label": "Markets",      "icon": "chart-line",     "module": "modules.stocks_module",   "enabled": True},
    {"id": "news",     "label": "World events", "icon": "world",          "module": "modules.news_module",     "enabled": True},
    # Coming soon — uncomment when ready:
    # {"id": "health", "label": "Health",       "icon": "heart-rate",     "module": "modules.health_module",   "enabled": False},
    # {"id": "calendar","label": "Calendar",    "icon": "calendar-event", "module": "modules.calendar_module", "enabled": False},
    # {"id": "crypto",  "label": "Crypto",      "icon": "currency-bitcoin","module": "modules.crypto_module",  "enabled": False},
]

def run():
    now = datetime.now()
    print(f"\n=== Daily Debrief — {now.strftime('%Y-%m-%d %H:%M')} ===\n")

    results = {}
    for cfg in MODULES:
        if not cfg["enabled"]:
            continue
        mid = cfg["id"]
        print(f"[{mid}] Running…")
        try:
            mod = importlib.import_module(cfg["module"])
            data = mod.fetch()
            results[mid] = {"status": "ok", "data": data, **cfg}
            print(f"[{mid}] Done.")
        except Exception as e:
            print(f"[{mid}] ERROR: {e}")
            traceback.print_exc()
            results[mid] = {"status": "error", "error": str(e), **cfg}

    html = build_dashboard(results, now)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\nindex.html written.")

if __name__ == "__main__":
    run()

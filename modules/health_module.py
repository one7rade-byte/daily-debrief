"""
Health module — plug in your wearable data source here.

Supported integrations (uncomment the one you use):
  - Apple Health export (XML file in repo)
  - Whoop API
  - Oura API
  - Garmin Connect
  - Manual CSV log

Right now this returns placeholder data so the dashboard
card renders. Replace fetch() body with your real source.
"""

import os

# Example: WHOOP_TOKEN = os.environ.get("WHOOP_TOKEN", "")
# Example: OURA_TOKEN  = os.environ.get("OURA_TOKEN", "")


def fetch():
    """
    Return a dict with your health metrics.
    All keys are optional — the builder renders whatever is present.
    """

    # ── Replace this block with your real data source ───────────
    # Example shape (fill in from your API/export):
    return {
        "source": "Manual",          # "Whoop" | "Oura" | "Apple Health" | etc.
        "ready": False,              # set True when you've wired a real source
        "metrics": [
            # {"label": "HRV",         "value": "68",  "unit": "ms",    "trend": "up"},
            # {"label": "Resting HR",  "value": "52",  "unit": "bpm",   "trend": "flat"},
            # {"label": "Sleep",       "value": "7h 20m","unit": "",     "trend": "down"},
            # {"label": "Recovery",    "value": "84",  "unit": "%",     "trend": "up"},
            # {"label": "Steps",       "value": "8,432","unit": "steps","trend": "flat"},
        ],
        "note": "Connect your wearable in modules/health_module.py to see stats here.",
    }

    # ── Whoop example (uncomment + add WHOOP_TOKEN secret) ──────
    # import requests
    # headers = {"Authorization": f"Bearer {WHOOP_TOKEN}"}
    # r = requests.get("https://api.prod.whoop.com/developer/v1/recovery/", headers=headers)
    # recovery = r.json()["records"][0]
    # return {
    #     "source": "Whoop",
    #     "ready": True,
    #     "metrics": [
    #         {"label": "Recovery", "value": str(recovery["score"]["recovery_score"]), "unit": "%", "trend": "up"},
    #         {"label": "HRV",      "value": str(round(recovery["score"]["hrv_rmssd_milli"])), "unit": "ms", "trend": "flat"},
    #     ],
    #     "note": "",
    # }

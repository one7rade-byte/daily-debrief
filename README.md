# Daily Debrief Dashboard

Personal dashboard that rebuilds every hour via GitHub Actions and serves on GitHub Pages.
One URL, works on any device, anywhere — same setup as the GEX tracker.

## What's included

| Module | Status | Data source |
|---|---|---|
| Inbox | ✅ Live | Gmail IMAP + Claude |
| Markets | ✅ Live | yfinance (free, no key) |
| World events | ✅ Live | BBC/NYT/Reuters RSS + Claude |
| Health | 🔜 Soon | Plug in Whoop / Oura / Apple Health |
| Calendar | 🔜 Soon | Google Calendar API |

## Adding a new module

1. Create `modules/your_module.py` with a `fetch()` function that returns a dict
2. Add a renderer `render_your_module(data)` in `builder.py`
3. Register it in the `MODULES` list in `main.py`
4. Add its name to `RENDERERS` dict in `builder.py`

That's it. The orchestrator picks it up automatically.

---

## Setup (same as GEX tracker)

### 1. Gmail App Password
- Gmail → Settings → Forwarding and POP/IMAP → Enable IMAP
- myaccount.google.com → Security → App Passwords → "Daily Debrief" → copy 16-char code

### 2. GitHub Secrets
Repo → Settings → Secrets → Actions → New repository secret:

| Secret | Value |
|---|---|
| `GMAIL_USER` | your@gmail.com |
| `GMAIL_PASS` | 16-char App Password |
| `ANTHROPIC_API_KEY` | sk-ant-... |

### 3. GitHub Pages
Repo → Settings → Pages → Source: main branch, root folder → Save

### 4. First run
Actions tab → Daily Debrief — Hourly → Run workflow

Your URL: `https://YOUR-USERNAME.github.io/daily-debrief/`

---

## Customizing

**Change stocks watchlist** — edit `WATCHLIST` in `modules/stocks_module.py`

**Change refresh frequency** — edit cron in `.github/workflows/debrief.yml`
- Every 2h: `'0 */2 * * *'`
- 9am + 6pm only: `'0 9,18 * * *'`

**Multiple Gmail accounts** — call `fetch_raw_emails()` twice with different credentials,
merge the lists before passing to `triage()` in `modules/email_module.py`

**Wire up health data** — see `modules/health_module.py` for Whoop/Oura examples

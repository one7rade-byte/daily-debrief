"""
Email module — fetches from 3 inboxes (2 Gmail + Yahoo IMAP),
triages all together with Gemini (free), labels each email by account.
Last 24 hours only, sorted latest to oldest per category.
"""

import imaplib, email, os, json, re
import urllib.request
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

MAX_PER_INBOX = 50


def get_accounts():
    return [
        {
            "id":    "gmail1",
            "label": os.environ.get("GMAIL_USER_1", "Gmail 1"),
            "user":  os.environ["GMAIL_USER_1"],
            "pass":  os.environ["GMAIL_PASS_1"],
            "host":  "imap.gmail.com",
            "color": "blue",
        },
        {
            "id":    "gmail2",
            "label": os.environ.get("GMAIL_USER_2", "Gmail 2"),
            "user":  os.environ["GMAIL_USER_2"],
            "pass":  os.environ["GMAIL_PASS_2"],
            "host":  "imap.gmail.com",
            "color": "purple",
        },
        {
            "id":    "yahoo",
            "label": os.environ.get("YAHOO_USER", "Yahoo"),
            "user":  os.environ["YAHOO_USER"],
            "pass":  os.environ["YAHOO_PASS"],
            "host":  "imap.mail.yahoo.com",
            "color": "amber",
        },
    ]


def decode_str(s):
    if not s: return ""
    parts = decode_header(s)
    out = []
    for part, enc in parts:
        if isinstance(part, bytes):
            out.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(str(part))
    return " ".join(out).strip()


def relative_time(dt):
    if not dt: return "unknown"
    try:
        diff = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    except Exception:
        return "unknown"
    s = int(diff.total_seconds())
    if s < 60:     return "just now"
    if s < 3600:   return f"{s // 60}m ago"
    if s < 86400:  return f"{s // 3600}h ago"
    return dt.strftime("%b %d %I:%M %p")


def get_snippet(msg, max_len=160):
    snippet = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = str(part.get("Content-Disposition", ""))
                if ct == "text/plain" and "attachment" not in cd:
                    raw = part.get_payload(decode=True)
                    if raw:
                        snippet = raw.decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                        break
        else:
            raw = msg.get_payload(decode=True)
            if raw:
                snippet = raw.decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )
    except Exception:
        pass
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet[:max_len] + ("…" if len(snippet) > max_len else "")


def fetch_from_account(account):
    emails = []
    print(f"  Connecting to {account['user']}...")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    # IMAP date search (SINCE = midnight of that date, good enough)
    since_str = cutoff.strftime("%d-%b-%Y")

    try:
        imap = imaplib.IMAP4_SSL(account["host"])
        imap.login(account["user"], account["pass"])
        imap.select("INBOX")

        # Search only last 24h using IMAP SINCE
        _, data = imap.search(None, f'SINCE "{since_str}"')
        all_ids = data[0].split()
        # Reverse so newest first
        ids = list(reversed(all_ids[-MAX_PER_INBOX:] if len(all_ids) > MAX_PER_INBOX else all_ids))

        _, unread_data = imap.search(None, "UNSEEN")
        unread_ids = set(unread_data[0].split())

        for uid in ids:
            try:
                _, msg_data = imap.fetch(uid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                from_raw = decode_str(msg.get("From", ""))
                nm = re.match(r'^"?([^"<]+)"?\s*<', from_raw)
                em = re.search(r"<([^>]+)>", from_raw)

                try:
                    dt = parsedate_to_datetime(msg.get("Date", ""))
                except Exception:
                    dt = None

                # Skip if actually older than 24h (SINCE is date-level not time-level)
                if dt and dt.astimezone(timezone.utc) < cutoff:
                    continue

                # Build the best possible Gmail link
                # Use X-GM-THRID if available (most reliable), else UID search
                if "gmail" in account["host"]:
                    # Fetch Gmail thread ID via IMAP extension
                    try:
                        _, th_data = imap.fetch(uid, "(X-GM-THRID)")
                        th_raw = th_data[0].decode() if th_data[0] else ""
                        th_match = re.search(r'X-GM-THRID (\d+)', th_raw)
                        if th_match:
                            thread_id = int(th_match.group(1))
                            # Convert to hex for Gmail URL
                            hex_id = format(thread_id, 'x')
                            link = f"https://mail.google.com/mail/u/0/#inbox/{hex_id}"
                        else:
                            link = f"https://mail.google.com/mail/u/0/#inbox"
                    except Exception:
                        link = "https://mail.google.com/mail/u/0/#inbox"
                elif "yahoo" in account["host"]:
                    link = "https://mail.yahoo.com/"
                else:
                    link = "#"

                emails.append({
                    "account_id":    account["id"],
                    "account_label": account["label"],
                    "account_color": account["color"],
                    "from_name":     nm.group(1).strip() if nm else from_raw.split("@")[0],
                    "from_email":    em.group(1) if em else from_raw,
                    "subject":       decode_str(msg.get("Subject", "(no subject)")),
                    "snippet":       get_snippet(msg),
                    "time":          relative_time(dt),
                    "timestamp":     dt.astimezone(timezone.utc).timestamp() if dt else 0,
                    "unread":        uid in unread_ids,
                    "gmail_link":    link,
                })
            except Exception as e:
                print(f"    Skip message: {e}")

        imap.logout()
        print(f"  Fetched {len(emails)} from {account['user']} (last 24h)")
    except Exception as e:
        print(f"  ERROR {account['user']}: {e}")

    return emails


def gemini(prompt):
    api_key = os.environ["GEMINI_API_KEY"]
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    raw = result["candidates"][0]["content"]["parts"][0]["text"]
    return re.sub(r"```json|```", "", raw).strip()


def triage(all_emails):
    listing = "\n".join(
        f"[{i}] [{e['account_label']}] FROM: {e['from_name']} <{e['from_email']}> "
        f"| SUBJECT: {e['subject']} | SNIPPET: {e['snippet']}"
        for i, e in enumerate(all_emails)
    )
    prompt = f"""Triage emails across 3 inboxes.

Priority:
- high: needs action — interviews, event confirmations, payments, real people waiting, job opportunities
- medium: useful FYI — shipping, bank statements, newsletters worth reading, receipts
- low: ignore — promos, spam, social notifications, ads, marketing

Tags (1-2 each): interview, action, event, finance, personal, work, social, spam, promo

Emails:
{listing}

Return ONLY valid JSON, no markdown fences:
{{"summary":"2-3 sentence overview across all inboxes mentioning most urgent items","classifications":[{{"index":0,"priority":"high","tags":["action"],"action":"one line what to do"}}]}}"""

    return json.loads(gemini(prompt))


def fetch():
    accounts = get_accounts()
    all_emails = []
    for account in accounts:
        all_emails.extend(fetch_from_account(account))

    if not all_emails:
        return {
            "summary":  "No emails in the last 24 hours.",
            "emails":   [],
            "accounts": [],
        }

    result = triage(all_emails)
    cls_map = {c["index"]: c for c in result.get("classifications", [])}

    merged = []
    for i, e in enumerate(all_emails):
        cls = cls_map.get(i, {})
        merged.append({
            **e,
            "priority": cls.get("priority", "low"),
            "tags":     cls.get("tags", []),
            "action":   cls.get("action", ""),
        })

    # Sort within each priority group by timestamp — newest first
    order = {"high": 0, "medium": 1, "low": 2}
    merged.sort(key=lambda e: (order.get(e["priority"], 2), -e.get("timestamp", 0)))

    return {
        "summary":  result.get("summary", ""),
        "emails":   merged,
        "accounts": [a["label"] for a in accounts],
    }

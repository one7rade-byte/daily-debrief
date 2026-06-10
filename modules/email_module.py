"""
Email module — fetches from 3 inboxes (2 Gmail + Yahoo IMAP),
triages all together with Claude, labels each email by account.
"""

import imaplib, email, os, json, re
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import anthropic

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
MAX_PER_INBOX = 20


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
    if s < 604800: return f"{s // 86400}d ago"
    return dt.strftime("%b %d")


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
    try:
        imap = imaplib.IMAP4_SSL(account["host"])
        imap.login(

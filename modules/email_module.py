"""
Email module — fetches Gmail via IMAP, triages with Claude.
Returns structured data consumed by the dashboard builder.
"""

import imaplib, email, os, json, re
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import anthropic

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_PASS"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
MAX_EMAILS = 35


def decode_str(s):
    if not s: return ""
    parts = decode_header(s)
    out = []
    for part, enc in parts:
        if isinstance(part, bytes):
            out.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(part)
    return " ".join(out)


def relative_time(dt):
    if not dt: return "unknown"
    try:
        diff = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    except Exception:
        return "unknown"
    s = int(diff.total_seconds())
    if s < 3600:   return f"{s//60}m ago"
    if s < 86400:  return f"{s//3600}h ago"
    if s < 604800: return f"{s//86400}d ago"
    return dt.strftime("%b %d")


def get_snippet(msg, max_len=160):
    snippet = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                    raw = part.get_payload(decode=True)
                    if raw:
                        snippet = raw.decode(part.get_content_charset() or "utf-8", errors="replace")
                        break
        else:
            raw = msg.get_payload(decode=True)
            if raw:
                snippet = raw.decode(msg.get_content_charset() or "utf-8", errors="replace")
    except Exception:
        pass
    snippet = re.sub(r'\s+', ' ', snippet).strip()
    return snippet[:max_len] + ("…" if len(snippet) > max_len else "")


def fetch_raw_emails():
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(GMAIL_USER, GMAIL_PASS)
    imap.select("INBOX")
    _, data = imap.search(None, "ALL")
    all_ids = data[0].split()
    ids = list(reversed(all_ids[-MAX_EMAILS:] if len(all_ids) > MAX_EMAILS else all_ids))
    _, unread_data = imap.search(None, "UNSEEN")
    unread_ids = set(unread_data[0].split())

    emails = []
    for uid in ids:
        try:
            _, msg_data = imap.fetch(uid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            from_raw = decode_str(msg.get("From", ""))
            nm = re.match(r'^"?([^"<]+)"?\s*<', from_raw)
            em = re.search(r'<([^>]+)>', from_raw)
            try:
                dt = parsedate_to_datetime(msg.get("Date", ""))
            except Exception:
                dt = None
            mid = msg.get("Message-ID", "").strip("<>")
            emails.append({
                "from_name":  nm.group(1).strip() if nm else from_raw.split("@")[0],
                "from_email": em.group(1) if em else from_raw,
                "subject":    decode_str(msg.get("Subject", "(no subject)")),
                "snippet":    get_snippet(msg),
                "time":       relative_time(dt),
                "unread":     uid in unread_ids,
                "gmail_link": f"https://mail.google.com/mail/u/0/#search/rfc822msgid%3A{mid}" if mid else "https://mail.google.com/mail/u/0/#inbox",
            })
        except Exception as e:
            print(f"  skip message: {e}")

    imap.logout()
    return emails


def triage(raw_emails):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    listing = "\n".join(
        f"[{i}] FROM: {e['from_name']} <{e['from_email']}> | SUBJECT: {e['subject']} | SNIPPET: {e['snippet']}"
        for i, e in enumerate(raw_emails)
    )
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": f"""Triage these emails. Rules:
- high: needs action — interviews, event confirmations, payments, real people waiting
- medium: useful FYI — shipping, bank statements, newsletters
- low: ignore — promos, spam, social notifications
Tags (1-2 each): interview, action, event, finance, personal, work, social, spam, promo

{listing}

Return ONLY JSON:
{{"summary":"2 sentence inbox overview","classifications":[{{"index":0,"priority":"high","tags":["action"],"action":"what to do in one line"}}]}}"""}]
    )
    raw = re.sub(r"```json|```", "", msg.content[0].text).strip()
    return json.loads(raw)


def fetch():
    """Entry point called by main.py. Returns dict consumed by builder."""
    raw = fetch_raw_emails()
    if not raw:
        return {"summary": "No emails found.", "emails": []}
    result = triage(raw)
    cls_map = {c["index"]: c for c in result.get("classifications", [])}
    emails = [{**e, "priority": cls_map.get(i, {}).get("priority", "low"),
                    "tags":     cls_map.get(i, {}).get("tags", []),
                    "action":   cls_map.get(i, {}).get("action", "")}
              for i, e in enumerate(raw)]
    return {"summary": result.get("summary", ""), "emails": emails}

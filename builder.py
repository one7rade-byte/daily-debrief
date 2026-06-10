"""
Dashboard builder — takes all module results and renders index.html.
Each module's card is a self-contained section. Adding a new module
only requires writing its render function here.
"""

import html as htmllib
import json
from datetime import datetime


# ── Module renderers ────────────────────────────────────────────

def render_email(data):
    emails = data.get("emails", [])
    summary = data.get("summary", "")
    if not emails:
        return '<div class="module-empty">No emails found.</div>'

    high   = [e for e in emails if e["priority"] == "high"]
    medium = [e for e in emails if e["priority"] == "medium"]
    low    = [e for e in emails if e["priority"] == "low"]
    unread = sum(1 for e in emails if e["unread"])

    def card(e):
        tags = "".join(f'<span class="tag tag-{htmllib.escape(t)}">{htmllib.escape(t)}</span>' for t in e.get("tags", []))
        action_html = f'<div class="email-action"><i class="ti ti-arrow-right"></i>{htmllib.escape(e["action"])}</div>' if e.get("action") and e["priority"] != "low" else ""
        av = {"high": "red", "medium": "amber"}.get(e["priority"], "blue")
        name = e.get("from_name", "?")
        parts = name.split()
        init = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()
        return f"""<a class="email-card {e['priority']}{'  unread' if e['unread'] else ''}" href="{htmllib.escape(e.get('gmail_link','#'))}" target="_blank" rel="noopener">
          <div class="avatar av-{av}">{htmllib.escape(init)}</div>
          <div class="email-body">
            <div class="ef">{htmllib.escape(e.get('from_name',''))}</div>
            <div class="ea">{htmllib.escape(e.get('from_email',''))}</div>
            <div class="es">{htmllib.escape(e.get('subject',''))}</div>
            <div class="ep">{htmllib.escape(e.get('snippet',''))}</div>
            {action_html}
            <div class="etags">{tags}</div>
          </div>
          <div class="email-right">
            <div class="etime">{htmllib.escape(e.get('time',''))}</div>
            <div class="eopen"><i class="ti ti-external-link"></i> Open</div>
          </div>
        </a>"""

    def sec(label, icon, items, cls):
        if not items: return ""
        return f'<div class="sec-lbl"><i class="ti ti-{icon}"></i>{label}<span class="sc {cls}">{len(items)}</span></div><div class="elist">{"".join(card(e) for e in items)}</div>'

    stats = f"""<div class="mod-stats">
      <div class="ms"><span class="msn cr">{len(high)}</span><span class="msl">Action needed</span></div>
      <div class="ms"><span class="msn ca">{len(medium)}</span><span class="msl">Watch</span></div>
      <div class="ms"><span class="msn cm">{len(low)}</span><span class="msl">Low priority</span></div>
      <div class="ms"><span class="msn">{unread}</span><span class="msl">Unread</span></div>
    </div>"""

    sum_html = f'<div class="mod-summary">{htmllib.escape(summary)}</div>' if summary else ""

    filters = """<div class="filters" id="email-filters">
      <button class="chip active" onclick="filterEmail('all',this)">All</button>
      <button class="chip cr" onclick="filterEmail('high',this)">Action</button>
      <button class="chip ca" onclick="filterEmail('medium',this)">Watch</button>
      <button class="chip" onclick="filterEmail('low',this)">Low</button>
      <button class="chip" onclick="filterEmail('unread',this)">Unread</button>
    </div>"""

    sections = sec("Action needed", "alert-circle", high, "red") + sec("Keep an eye on", "eye", medium, "amber") + sec("Low priority", "inbox", low, "muted")

    return f'{stats}{sum_html}{filters}<div id="email-cards" data-emails="{htmllib.escape(json.dumps(emails))}">{sections}</div>'


def render_stocks(data):
    tickers = data.get("tickers", [])
    market_open = data.get("market_open", False)
    as_of = data.get("as_of", "")
    if not tickers:
        return '<div class="module-empty">No market data available.</div>'

    status = '<span class="market-open">Market open</span>' if market_open else '<span class="market-closed">Market closed</span>'
    tiles = ""
    for t in tickers:
        d = t["direction"]
        arrow = "ti-trending-up" if d == "up" else "ti-trending-down" if d == "down" else "ti-minus"
        cls   = "up" if d == "up" else "down" if d == "down" else "flat"
        tiles += f"""<div class="ticker-tile">
          <div class="tt-label">{htmllib.escape(t['label'])}</div>
          <div class="tt-val">{htmllib.escape(t['value'])}</div>
          <div class="tt-chg {cls}"><i class="ti {arrow}"></i>{htmllib.escape(t['change'])}</div>
        </div>"""

    return f'<div class="mod-meta">{status} · as of {as_of}</div><div class="ticker-grid">{tiles}</div>'


def render_news(data):
    briefing = data.get("briefing", "")
    stories  = data.get("stories", [])
    if not stories:
        return '<div class="module-empty">No news stories available.</div>'

    cat_icon = {"world":"world","us":"building","markets":"chart-bar","tech":"cpu","science":"flask","conflict":"alert-triangle"}
    cards = ""
    for s in stories:
        cat  = s.get("category", "world")
        icon = cat_icon.get(cat, "news")
        link = s.get("link", "#")
        cards += f"""<a class="story-card" href="{htmllib.escape(link)}" target="_blank" rel="noopener">
          <div class="story-cat cat-{cat}"><i class="ti ti-{icon}"></i>{cat}</div>
          <div class="story-title">{htmllib.escape(s.get('title',''))}</div>
          <div class="story-sum">{htmllib.escape(s.get('summary',''))}</div>
          <div class="story-src">{htmllib.escape(s.get('source',''))}</div>
        </a>"""

    brief_html = f'<div class="mod-summary">{htmllib.escape(briefing)}</div>' if briefing else ""
    return f'{brief_html}<div class="story-grid">{cards}</div>'


def render_health(data):
    if not data.get("ready"):
        note = data.get("note", "")
        return f'<div class="module-empty"><i class="ti ti-plug" style="font-size:20px;display:block;margin-bottom:8px"></i>{htmllib.escape(note)}</div>'
    metrics = data.get("metrics", [])
    source  = data.get("source", "")
    tiles = ""
    for m in metrics:
        trend = m.get("trend", "flat")
        arrow = "ti-trending-up" if trend == "up" else "ti-trending-down" if trend == "down" else "ti-minus"
        cls   = "up" if trend == "up" else "down" if trend == "down" else "flat"
        tiles += f"""<div class="health-tile">
          <div class="ht-label">{htmllib.escape(m['label'])}</div>
          <div class="ht-val">{htmllib.escape(m['value'])} <span class="ht-unit">{htmllib.escape(m.get('unit',''))}</span></div>
          <div class="ht-trend {cls}"><i class="ti {arrow}"></i></div>
        </div>"""
    return f'<div class="mod-meta">Source: {htmllib.escape(source)}</div><div class="health-grid">{tiles}</div>'


RENDERERS = {
    "email":  render_email,
    "stocks": render_stocks,
    "news":   render_news,
    "health": render_health,
}


# ── Main builder ────────────────────────────────────────────────

def build_dashboard(results, now: datetime) -> str:
    now_str   = now.strftime("%A, %B %d · %I:%M %p")
    date_str  = now.strftime("%Y-%m-%d %H:%M UTC")

    # Build nav + sections
    nav_items = ""
    sections  = ""

    for mid, res in results.items():
        label  = res.get("label", mid)
        icon   = res.get("icon", "layout")
        status = res.get("status", "error")

        nav_items += f'<a class="nav-item" href="#{mid}" onclick="showSection(\'{mid}\',this)">'
        nav_items += f'<i class="ti ti-{icon}"></i><span>{label}</span></a>'

        if status == "error":
            body = f'<div class="module-empty error"><i class="ti ti-alert-circle"></i> {htmllib.escape(res.get("error","Unknown error"))}</div>'
        else:
            renderer = RENDERERS.get(mid)
            body = renderer(res["data"]) if renderer else '<div class="module-empty">No renderer for this module.</div>'

        sections += f'<section class="mod-section" id="section-{mid}"><div class="mod-body">{body}</div></section>'

    first_id = list(results.keys())[0] if results else ""

    # Inline email data for JS filtering
    email_data_script = ""
    if "email" in results and results["email"].get("status") == "ok":
        email_data_script = f"const EMAIL_DATA = {json.dumps(results['email']['data'].get('emails',[]))};"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<title>Daily Debrief</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/tabler-icons.min.css">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0c0c0f;--s1:#15151a;--s2:#1d1d24;--s3:#25252e;
  --b1:rgba(255,255,255,0.06);--b2:rgba(255,255,255,0.11);--b3:rgba(255,255,255,0.18);
  --text:#eeedf3;--muted:#8988a0;--dim:#4e4d5e;
  --accent:#7f77dd;--ad:rgba(127,119,221,0.16);
  --red:#e24b4a;--rd:rgba(226,75,74,0.12);
  --amber:#d4962a;--amd:rgba(212,150,42,0.12);
  --green:#1d9e75;--gd:rgba(29,158,117,0.12);
  --blue:#378add;--bd:rgba(55,138,221,0.12);
  --r:12px;--rsm:7px;--rxs:5px;
}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',-apple-system,sans-serif;min-height:100vh;display:flex;flex-direction:column}}

/* ── Top bar ── */
.topbar{{display:flex;align-items:center;justify-content:space-between;padding:0 1.5rem;height:56px;border-bottom:0.5px solid var(--b1);flex-shrink:0;gap:1rem}}
.topbar-brand{{display:flex;align-items:center;gap:8px;font-weight:600;font-size:15px}}
.topbar-brand i{{font-size:18px;color:var(--accent)}}
.topbar-meta{{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:8px}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.countdown{{font-size:11px;color:var(--dim)}}

/* ── Layout ── */
.layout{{display:flex;flex:1;min-height:0}}

/* ── Sidebar nav ── */
.sidebar{{width:200px;flex-shrink:0;border-right:0.5px solid var(--b1);padding:1.25rem 0;display:flex;flex-direction:column;gap:2px}}
.nav-item{{display:flex;align-items:center;gap:10px;padding:9px 1.25rem;font-size:13px;font-weight:500;color:var(--muted);cursor:pointer;transition:all .15s;border-right:2px solid transparent;text-decoration:none}}
.nav-item i{{font-size:16px}}
.nav-item:hover{{color:var(--text);background:var(--s2)}}
.nav-item.active{{color:var(--accent);background:var(--ad);border-right-color:var(--accent)}}
.nav-coming{{display:flex;align-items:center;gap:10px;padding:9px 1.25rem;font-size:12px;color:var(--dim);margin-top:auto}}
.nav-coming i{{font-size:15px}}
.soon-badge{{font-size:9px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;background:var(--s3);color:var(--dim);padding:1px 5px;border-radius:3px}}

/* ── Main content ── */
.main{{flex:1;overflow-y:auto;padding:1.75rem}}
.mod-section{{display:none;max-width:860px}}
.mod-section.visible{{display:block}}
.mod-body{{}}

/* ── Module common ── */
.module-empty{{text-align:center;padding:2.5rem 1rem;font-size:13px;color:var(--muted);line-height:1.7}}
.module-empty.error{{color:var(--red);background:var(--rd);border-radius:var(--rsm);padding:1rem 1.25rem;text-align:left;display:flex;align-items:center;gap:8px}}
.mod-summary{{background:var(--s1);border:0.5px solid var(--b1);border-left:3px solid var(--accent);border-radius:0 var(--rsm) var(--rsm) 0;padding:12px 16px;font-size:13px;color:var(--muted);line-height:1.7;margin-bottom:1.25rem}}
.mod-meta{{font-size:11px;color:var(--dim);margin-bottom:1rem;display:flex;align-items:center;gap:8px}}
.mod-stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:1.25rem}}
.ms{{background:var(--s1);border:0.5px solid var(--b1);border-radius:var(--rsm);padding:12px 14px}}
.msn{{display:block;font-size:24px;font-weight:600}}
.msn.cr{{color:var(--red)}}.msn.ca{{color:var(--amber)}}.msn.cm{{color:var(--muted)}}
.msl{{font-size:11px;color:var(--muted);margin-top:2px;display:block}}

/* ── Email ── */
.filters{{display:flex;gap:6px;margin-bottom:1rem;flex-wrap:wrap}}
.chip{{padding:4px 12px;border-radius:99px;font-size:12px;font-weight:500;border:0.5px solid var(--b2);background:transparent;color:var(--muted);cursor:pointer;transition:all .15s}}
.chip:hover,.chip.active{{background:var(--s2);color:var(--text);border-color:var(--b3)}}
.chip.cr.active{{background:var(--rd);color:var(--red);border-color:var(--red)}}
.chip.ca.active{{background:var(--amd);color:var(--amber);border-color:var(--amber)}}
.sec-lbl{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:600;color:var(--muted);display:flex;align-items:center;gap:7px;margin:1.5rem 0 9px}}
.sec-lbl:first-child{{margin-top:0}}
.sec-lbl i{{font-size:14px}}
.sc{{font-size:11px;font-weight:500;padding:1px 7px;border-radius:99px;letter-spacing:0;text-transform:none}}
.sc.red{{background:var(--rd);color:var(--red)}}.sc.amber{{background:var(--amd);color:var(--amber)}}.sc.muted{{background:var(--s3);color:var(--muted)}}
.elist{{display:flex;flex-direction:column;gap:7px}}
.email-card{{background:var(--s1);border:0.5px solid var(--b1);border-radius:var(--r);padding:12px 14px;display:grid;grid-template-columns:38px 1fr auto;gap:0 11px;align-items:start;text-decoration:none;transition:border-color .15s,background .15s}}
.email-card:hover{{border-color:var(--b2);background:var(--s2)}}
.email-card.high{{border-left:2.5px solid var(--red)}}
.email-card.medium{{border-left:2.5px solid var(--amber)}}
.email-card.unread{{border-left:2.5px solid var(--blue)}}
.avatar{{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;flex-shrink:0;margin-top:1px}}
.av-red{{background:var(--rd);color:var(--red)}}.av-amber{{background:var(--amd);color:var(--amber)}}.av-blue{{background:var(--bd);color:var(--blue)}}
.ef{{font-size:13px;font-weight:500;color:var(--text)}}.ea{{font-size:11px;color:var(--dim);margin-top:1px}}
.es{{font-size:13px;color:var(--text);margin-top:4px;line-height:1.4}}.ep{{font-size:12px;color:var(--muted);margin-top:3px;line-height:1.5}}
.email-action{{font-size:11px;color:var(--amber);margin-top:5px;display:flex;align-items:center;gap:5px}}
.email-action i{{font-size:12px}}
.etags{{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}}
.tag{{font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding:2px 6px;border-radius:99px;background:var(--s3);color:var(--dim)}}
.tag-interview{{background:var(--amd);color:var(--amber)}}.tag-action{{background:var(--rd);color:var(--red)}}
.tag-event{{background:var(--gd);color:var(--green)}}.tag-finance{{background:var(--bd);color:var(--blue)}}
.tag-personal,.tag-work{{background:var(--ad);color:var(--accent)}}
.email-right{{text-align:right;flex-shrink:0;padding-top:2px}}
.etime{{font-size:11px;color:var(--dim)}}.eopen{{font-size:11px;color:var(--accent);margin-top:5px;display:inline-flex;align-items:center;gap:3px}}

/* ── Stocks ── */
.market-open{{color:var(--green);font-weight:500}}.market-closed{{color:var(--dim)}}
.ticker-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px}}
.ticker-tile{{background:var(--s1);border:0.5px solid var(--b1);border-radius:var(--rsm);padding:13px 15px}}
.tt-label{{font-size:11px;color:var(--muted);margin-bottom:4px}}.tt-val{{font-size:20px;font-weight:600}}
.tt-chg{{font-size:12px;margin-top:3px;display:flex;align-items:center;gap:4px}}
.tt-chg i{{font-size:13px}}.up{{color:var(--green)}}.down{{color:var(--red)}}.flat{{color:var(--muted)}}

/* ── News ── */
.story-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}}
.story-card{{background:var(--s1);border:0.5px solid var(--b1);border-radius:var(--r);padding:13px 14px;text-decoration:none;display:flex;flex-direction:column;gap:7px;transition:border-color .15s,background .15s}}
.story-card:hover{{border-color:var(--b2);background:var(--s2)}}
.story-cat{{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;display:flex;align-items:center;gap:5px}}
.story-cat i{{font-size:12px}}
.cat-world{{color:#5DCAA5}}.cat-us{{color:var(--blue)}}.cat-markets{{color:var(--amber)}}
.cat-tech{{color:var(--accent)}}.cat-science{{color:#5bc4e0}}.cat-conflict{{color:var(--red)}}
.story-title{{font-size:13px;font-weight:500;color:var(--text);line-height:1.4}}
.story-sum{{font-size:12px;color:var(--muted);line-height:1.55}}
.story-src{{font-size:11px;color:var(--dim);margin-top:auto}}

/* ── Health ── */
.health-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}}
.health-tile{{background:var(--s1);border:0.5px solid var(--b1);border-radius:var(--rsm);padding:13px 15px;display:flex;flex-direction:column;gap:4px}}
.ht-label{{font-size:11px;color:var(--muted)}}.ht-val{{font-size:20px;font-weight:600;color:var(--text)}}
.ht-unit{{font-size:13px;font-weight:400;color:var(--muted)}}.ht-trend{{font-size:14px}}

@media(max-width:640px){{
  .sidebar{{display:none}}.topbar-meta .countdown{{display:none}}
  .mod-stats{{grid-template-columns:repeat(2,1fr)}}
  .email-card{{grid-template-columns:36px 1fr}}.email-right{{display:none}}
}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-brand"><i class="ti ti-layout-dashboard"></i> Daily Debrief</div>
  <div class="topbar-meta">
    <span class="live-dot"></span>
    {now_str}
    <span class="countdown" id="countdown"></span>
  </div>
</div>

<div class="layout">
  <nav class="sidebar">
    {nav_items}
    <div class="nav-coming"><i class="ti ti-heart-rate"></i>Health <span class="soon-badge">soon</span></div>
    <div class="nav-coming"><i class="ti ti-calendar-event"></i>Calendar <span class="soon-badge">soon</span></div>
  </nav>

  <main class="main">
    {sections}
  </main>
</div>

<script>
{email_data_script}

function showSection(id, el) {{
  document.querySelectorAll('.mod-section').forEach(s => s.classList.remove('visible'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const sec = document.getElementById('section-' + id);
  if (sec) sec.classList.add('visible');
  if (el) el.classList.add('active');
}}

// Activate first section
showSection('{first_id}', document.querySelector('.nav-item'));

// Email filter
function filterEmail(f, el) {{
  document.querySelectorAll('#email-filters .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  if (typeof EMAIL_DATA === 'undefined') return;
  let filtered = EMAIL_DATA;
  if (f === 'high')   filtered = EMAIL_DATA.filter(e => e.priority === 'high');
  if (f === 'medium') filtered = EMAIL_DATA.filter(e => e.priority === 'medium');
  if (f === 'low')    filtered = EMAIL_DATA.filter(e => e.priority === 'low');
  if (f === 'unread') filtered = EMAIL_DATA.filter(e => e.unread);

  function initials(n) {{ const p=n.trim().split(/\s+/); return p.length>=2?(p[0][0]+p[p.length-1][0]).toUpperCase():n.slice(0,2).toUpperCase(); }}
  function av(p) {{ return {{high:'red',medium:'amber'}}[p]||'blue'; }}
  const tagCls = {{interview:'tag-interview',action:'tag-action',event:'tag-event',finance:'tag-finance',personal:'tag-personal',work:'tag-work'}};

  function card(e) {{
    const tags = (e.tags||[]).map(t=>`<span class="tag ${{tagCls[t]||''}}">${{t}}</span>`).join('');
    const act = (e.action&&e.priority!=='low')?`<div class="email-action"><i class="ti ti-arrow-right"></i>${{e.action}}</div>`:'';
    return `<a class="email-card ${{e.priority}}${{e.unread?' unread':''}}" href="${{e.gmail_link}}" target="_blank" rel="noopener">
      <div class="avatar av-${{av(e.priority)}}">${{initials(e.from_name)}}</div>
      <div class="email-body">
        <div class="ef">${{e.from_name}}</div><div class="ea">${{e.from_email}}</div>
        <div class="es">${{e.subject}}</div><div class="ep">${{e.snippet}}</div>
        ${{act}}<div class="etags">${{tags}}</div>
      </div>
      <div class="email-right"><div class="etime">${{e.time}}</div><div class="eopen"><i class="ti ti-external-link"></i> Open</div></div>
    </a>`;
  }}

  function sec(label, icon, items, cls) {{
    if(!items.length) return '';
    return `<div class="sec-lbl"><i class="ti ti-${{icon}}"></i>${{label}}<span class="sc ${{cls}}">${{items.length}}</span></div><div class="elist">${{items.map(card).join('')}}</div>`;
  }}

  const high=filtered.filter(e=>e.priority==='high'), med=filtered.filter(e=>e.priority==='medium'), low=filtered.filter(e=>e.priority==='low');
  document.getElementById('email-cards').innerHTML =
    sec('Action needed','alert-circle',high,'red')+sec('Keep an eye on','eye',med,'amber')+sec('Low priority','inbox',low,'muted') ||
    '<div class="module-empty">No emails in this view.</div>';
}}

// Countdown
(function() {{
  const target = Date.now() + 3600000;
  setInterval(() => {{
    const d = Math.max(0,Math.round((target-Date.now())/1000));
    document.getElementById('countdown').textContent = `· refresh in ${{Math.floor(d/60)}}:${{String(d%60).padStart(2,'0')}}`;
  }}, 1000);
}})();
</script>
</body>
</html>"""

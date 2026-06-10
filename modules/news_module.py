"""
News module — pulls top stories from RSS feeds, summarizes with Claude.
No API key needed for fetching. Claude writes the briefing.
"""

import os, json, re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import anthropic

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

# ── RSS feeds (free, no keys) ───────────────────────────────────
FEEDS = [
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",       "source": "BBC World"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "source": "NYT World"},
    {"url": "https://feeds.reuters.com/reuters/businessNews",     "source": "Reuters Business"},
    {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml",  "source": "BBC Tech"},
]

MAX_STORIES = 20  # stories sent to Claude for summarization


def parse_feed(url, source):
    stories = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            tree = ET.parse(resp)
        root = tree.getroot()
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item")
        for item in items[:6]:
            title = (item.findtext("title") or "").strip()
            desc  = re.sub(r'<[^>]+>', '', item.findtext("description") or "").strip()
            link  = (item.findtext("link") or "").strip()
            pub   = (item.findtext("pubDate") or "").strip()
            if title:
                stories.append({"title": title, "desc": desc[:200], "link": link, "source": source, "pub": pub})
    except Exception as e:
        print(f"  Feed error ({source}): {e}")
    return stories


def fetch():
    # Gather stories from all feeds
    all_stories = []
    for feed in FEEDS:
        all_stories.extend(parse_feed(feed["url"], feed["source"]))

    if not all_stories:
        return {"summary": "Could not fetch news feeds.", "stories": []}

    top = all_stories[:MAX_STORIES]

    # Ask Claude to summarize and classify
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    listing = "\n".join(
        f"[{i}] [{s['source']}] {s['title']} — {s['desc']}"
        for i, s in enumerate(top)
    )

    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""You are a world events briefing editor. Today is {datetime.now().strftime('%B %d, %Y')}.

Here are today's top stories:
{listing}

1. Write a 2-sentence overall briefing covering the most important themes.
2. Pick the 6 most significant stories. For each: write a sharp 1-sentence summary and assign a category.
   Categories: world, us, markets, tech, science, conflict

Return ONLY JSON:
{{"briefing":"...","stories":[{{"index":0,"category":"world","summary":"1 sentence"}}]}}"""}]
    )

    raw = re.sub(r"```json|```", "", msg.content[0].text).strip()
    result = json.loads(raw)

    # Merge with original stories for links
    output_stories = []
    for s in result.get("stories", []):
        i = s.get("index", 0)
        orig = top[i] if i < len(top) else {}
        output_stories.append({
            "title":    orig.get("title", ""),
            "summary":  s.get("summary", ""),
            "category": s.get("category", "world"),
            "source":   orig.get("source", ""),
            "link":     orig.get("link", ""),
        })

    return {"briefing": result.get("briefing", ""), "stories": output_stories}

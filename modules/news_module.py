"""
News module — pulls top stories from RSS feeds, summarizes with Gemini (free).
"""

import os, json, re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FEEDS = [
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",           "source": "BBC World"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "source": "NYT World"},
    {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml",      "source": "BBC Tech"},
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",        "source": "BBC Business"},
]

MAX_STORIES = 20


def parse_feed(url, source):
    stories = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            tree = ET.parse(resp)
        root = tree.getroot()
        for item in root.findall(".//item")[:6]:
            title = (item.findtext("title") or "").strip()
            desc  = re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()
            link  = (item.findtext("link") or "").strip()
            if title:
                stories.append({
                    "title":  title,
                    "desc":   desc[:200],
                    "link":   link,
                    "source": source,
                })
    except Exception as e:
        print(f"  Feed error ({source}): {e}")
    return stories


def gemini(prompt):
    api_key = os.environ["GEMINI_API_KEY"]
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    raw = result["candidates"][0]["content"]["parts"][0]["text"]
    return re.sub(r"```json|```", "", raw).strip()


def fetch():
    all_stories = []
    for feed in FEEDS:
        all_stories.extend(parse_feed(feed["url"], feed["source"]))

    if not all_stories:
        return {"briefing": "Could not fetch news feeds.", "stories": []}

    top = all_stories[:MAX_STORIES]
    listing = "\n".join(
        f"[{i}] [{s['source']}] {s['title']} — {s['desc']}"
        for i, s in enumerate(top)
    )

    prompt = f"""You are a world events briefing editor. Today is {datetime.now().strftime('%B %d, %Y')}.

Stories:
{listing}

1. Write a 2-sentence overall briefing covering the most important themes.
2. Pick the 6 most significant stories. For each write a sharp 1-sentence summary and assign a category.
Categories: world, us, markets, tech, science, conflict

Return ONLY valid JSON, no markdown fences:
{{"briefing":"...","stories":[{{"index":0,"category":"world","summary":"1 sentence"}}]}}"""

    parsed = json.loads(gemini(prompt))

    output_stories = []
    for s in parsed.get("stories", []):
        i = s.get("index", 0)
        orig = top[i] if i < len(top) else {}
        output_stories.append({
            "title":    orig.get("title", ""),
            "summary":  s.get("summary", ""),
            "category": s.get("category", "world"),
            "source":   orig.get("source", ""),
            "link":     orig.get("link", ""),
        })

    return {"briefing": parsed.get("briefing", ""), "stories": output_stories}

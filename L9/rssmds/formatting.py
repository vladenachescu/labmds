import json
import html
import re
import textwrap
from datetime import datetime
from typing import Any, Sequence


def format_entry_line(entry: Any, width: int = 80) -> str:
    read_marker = " " if entry["read"] else "*"
    entry_id = f"[{entry['id']}]"
    feed: str = entry["feed_title"] or "?"

    date_str = ""
    if entry["published"]:
        try:
            dt = datetime.fromisoformat(entry["published"])
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            date_str = entry["published"][:16]

    title: str = entry["title"] or "(untitled)"
    header = f"{read_marker} {entry_id:>6} {date_str:>16}  {feed}"

    available = width - len(header) - 3
    if available > 10:
        if len(title) > available:
            title = title[:available - 3] + "..."
    line = f"{header}  {title}"
    return line


def format_entry_detail(entry: Any) -> str:
    lines: list[str] = []
    lines.append(f"Title:     {entry['title']}")
    lines.append(f"Feed:      {entry['feed_title']}")
    lines.append(f"Link:      {entry['link']}")
    lines.append(f"Published: {entry['published'] or 'unknown'}")
    lines.append(f"Status:    {'read' if entry['read'] else 'unread'}")
    lines.append("")

    summary: str = entry["summary"] or "(no summary)"
    summary = _strip_html(summary)
    wrapped = textwrap.fill(summary, width=78)
    lines.append(wrapped)

    return "\n".join(lines)


def format_feed_list(feeds: Sequence[Any]) -> str:
    lines: list[str] = []
    for feed in feeds:
        feed_id = f"[{feed['id']}]"
        title: str = feed["title"] or "(untitled)"
        url: str = feed["url"]
        fetched: str = feed["last_fetched"] or "never"
        lines.append(f"{feed_id:>6}  {title}")
        lines.append(f"        {url}")
        lines.append(f"        Last fetched: {fetched}")
        lines.append("")
    return "\n".join(lines)


def format_stats(stats: Sequence[Any]) -> str:
    lines: list[str] = []
    total_entries = 0
    total_unread = 0

    for row in stats:
        title: str = row["title"] or row["url"]
        total: int = row["total"]
        unread: int = row["unread"]
        total_entries += total
        total_unread += unread
        lines.append(f"  {title}: {total} entries, {unread} unread")

    header = f"Feeds: {len(stats)}  |  Entries: {total_entries}  |  Unread: {total_unread}"
    return header + "\n" + "\n".join(lines)


def export_json(entries: Sequence[Any]) -> str:
    data: list[dict[str, Any]] = []
    for e in entries:
        data.append({
            "id": e["id"],
            "title": e["title"],
            "link": e["link"],
            "summary": e["summary"],
            "published": e["published"],
            "read": bool(e["read"]),
            "feed": e["feed_title"],
        })
    return json.dumps(data, indent=2, ensure_ascii=False)


def export_opml(feeds: Sequence[Any]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        '<head><title>rssmds subscriptions</title></head>',
        '<body>',
    ]
    for feed in feeds:
        title = html.escape(feed["title"] or "")
        url = html.escape(feed["url"])
        lines.append(f'  <outline type="rss" text="{title}" xmlUrl="{url}" />')
    lines.append('</body>')
    lines.append('</opml>')
    return "\n".join(lines)


def _strip_html(text: str) -> str:
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<p\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return text.strip()

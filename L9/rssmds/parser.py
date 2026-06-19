import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime


ATOM_NS = "http://www.w3.org/2005/Atom"

EntryDict = dict[str, str | None]


def parse_feed(xml_text: str) -> tuple[str | None, list[EntryDict]]:
    root = ET.fromstring(xml_text)

    if root.tag == "rss" or root.tag == "rdf":
        return _parse_rss(root)
    elif root.tag == f"{{{ATOM_NS}}}feed" or root.tag == "feed":
        return _parse_atom(root)
    else:
        raise ValueError(f"Unknown feed format: {root.tag}")


def _parse_rss(root: ET.Element) -> tuple[str | None, list[EntryDict]]:
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS feed missing <channel>")

    feed_title = _text(channel, "title")
    entries: list[EntryDict] = []

    for item in channel.findall("item"):
        guid = _text(item, "guid") or _text(item, "link")
        if not guid:
            continue

        pub_date = _text(item, "pubDate")
        published = _parse_date(pub_date) if pub_date else None

        entries.append({
            "guid": guid,
            "title": _text(item, "title") or "(untitled)",
            "link": _text(item, "link") or "",
            "summary": _text(item, "description") or "",
            "published": published,
        })

    return feed_title, entries


def _parse_atom(root: ET.Element) -> tuple[str | None, list[EntryDict]]:
    ns = ""
    if root.tag.startswith("{"):
        ns = f"{{{ATOM_NS}}}"

    feed_title = _text(root, f"{ns}title")
    entries: list[EntryDict] = []

    for entry in root.findall(f"{ns}entry"):
        entry_id = _text(entry, f"{ns}id")
        if not entry_id:
            continue

        link_el = entry.find(f"{ns}link[@rel='alternate']")
        if link_el is None:
            link_el = entry.find(f"{ns}link")
        link = link_el.get("href", "") if link_el is not None else ""

        summary_el = entry.find(f"{ns}summary")
        if summary_el is None:
            summary_el = entry.find(f"{ns}content")
        summary = summary_el.text or "" if summary_el is not None else ""

        updated = _text(entry, f"{ns}updated") or _text(entry, f"{ns}published")
        published = _parse_date(updated) if updated else None

        entries.append({
            "guid": entry_id,
            "title": _text(entry, f"{ns}title") or "(untitled)",
            "link": link,
            "summary": summary,
            "published": published,
        })

    return feed_title, entries


def _text(parent: ET.Element, tag: str) -> str | None:
    el = parent.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return None


def _parse_date(date_str: str | None) -> str | None:
    if not date_str:
        return None

    # RFC 2822 (common in RSS)
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except (ValueError, TypeError):
        pass

    # ISO 8601 / RFC 3339 (common in Atom)
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            return datetime.strptime(date_str, fmt).isoformat()
        except ValueError:
            continue

    return date_str

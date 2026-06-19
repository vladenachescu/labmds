import sqlite3
from typing import Any, Callable

import requests

from .parser import parse_feed


DEFAULT_TIMEOUT = 15
USER_AGENT = "rssmds/0.1"

FetchResult = dict[str, str | None | list[dict[str, str | None]]]


def fetch_feed(
    url: str,
    etag: str | None = None,
    last_modified: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> FetchResult | None:
    headers: dict[str, str] = {"User-Agent": USER_AGENT}

    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    response = requests.get(url, headers=headers, timeout=timeout)

    if response.status_code == 304:
        return None

    response.raise_for_status()

    new_etag = response.headers.get("ETag")
    new_last_modified = response.headers.get("Last-Modified")

    feed_title, entries = parse_feed(response.text)

    return {
        "title": feed_title,
        "entries": entries,
        "etag": new_etag,
        "last_modified": new_last_modified,
    }


def fetch_all(
    conn: sqlite3.Connection,
    feeds: list[Any],
    on_progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    from . import db

    results: dict[str, Any] = {"updated": 0, "unchanged": 0, "errors": []}

    for feed in feeds:
        feed_id: int = feed["id"]
        url: str = feed["url"]

        full_feed = db.get_feed(conn, feed_id)

        if on_progress:
            on_progress(f"Fetching {url}...")

        try:
            data = fetch_feed(
                url,
                etag=full_feed["etag"] if full_feed else None,
                last_modified=full_feed["last_modified"] if full_feed else None,
            )
        except Exception as e:
            results["errors"].append((url, str(e)))
            continue

        if data is None:
            results["unchanged"] += 1
            continue

        db.update_feed_meta(
            conn, feed_id,
            title=str(data["title"]) if data["title"] else None,
            etag=str(data["etag"]) if data["etag"] else None,
            last_modified=str(data["last_modified"]) if data["last_modified"] else None,
        )

        new_count = 0
        entries: list[Any] = data["entries"]  # type: ignore[assignment]
        for entry in entries:
            was_new = db.upsert_entry(
                conn, feed_id,
                guid=entry["guid"],
                title=entry["title"],
                link=entry["link"],
                summary=entry["summary"],
                published=entry["published"],
            )
            if was_new:
                new_count += 1

        conn.commit()
        results["updated"] += 1

        if on_progress:
            on_progress(f"  {len(entries)} entries ({new_count} new)")

    return results

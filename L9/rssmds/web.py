from __future__ import annotations

import html as html_module
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse, parse_qs

from . import db as database
from .formatting import _strip_html


_conn: sqlite3.Connection | None = None


class FeedrHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/" or path == "":
            self._handle_index(params)
        elif path == "/feeds":
            self._handle_feeds()
        elif path.startswith("/entry/"):
            self._handle_entry(path)
        elif path == "/stats":
            self._handle_stats()
        elif path == "/style.css":
            self._serve_css()
        elif path.startswith("/api/"):
            self._handle_api(path, params)
        else:
            self._send_response(404, "<h1>Not found</h1>")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else ""

        if path == "/add":
            self._handle_add_feed(body)
        elif path.startswith("/remove/"):
            self._handle_remove_feed(path)
        elif path.startswith("/mark-read/"):
            self._handle_mark_read(path)
        elif path == "/mark-all-read":
            self._handle_mark_all_read()
        else:
            self._send_response(404, "<h1>Not found</h1>")

    def _handle_index(self, params: dict[str, list[str]]) -> None:
        assert _conn is not None
        parsed_url = urlparse(self.path)
        feed_filter: str | None = params.get("feed", [None])[0]
        search_query: str | None = params.get("q", [None])[0]
        unread_only = "unread" in parsed_url.query

        feed_id = int(feed_filter) if feed_filter else None
        if search_query:
            entries = database.search_entries(_conn, search_query, limit=100)
        else:
            entries = database.list_entries(
                _conn, feed_id=feed_id, unread_only=unread_only, limit=100,
            )
        feeds = database.list_feeds(_conn)

        rows: list[str] = []
        for e in entries:
            read_class = "read" if e["read"] else "unread"
            title: str = e["title"] or "(untitled)"
            feed_title: str = e["feed_title"] or "?"
            published: str = (e["published"] or "")[:16]
            summary = _strip_html(e["summary"] or "")[:200]

            rows.append(f"""
                <tr class="{read_class}">
                    <td class="entry-date">{published}</td>
                    <td class="entry-feed">{_esc(feed_title)}</td>
                    <td>
                        <a href="/entry/{e['id']}">{_esc(title)}</a>
                        <div class="summary">{_esc(summary)}</div>
                    </td>
                </tr>
            """)

        feed_options = ['<option value="">All feeds</option>']
        for f in feeds:
            selected = "selected" if feed_filter and int(feed_filter) == f["id"] else ""
            name = _esc(f["title"] or f["url"])
            feed_options.append(
                f'<option value="{f["id"]}" {selected}>{name}</option>'
            )

        unread_checked = "checked" if unread_only else ""

        page_html = _page("Entries", f"""
            <div class="toolbar">
                <form method="get" action="/">
                    <input type="text" name="q" placeholder="Search entries..." value="{_esc(search_query or '')}" style="margin-right: 0.5rem;">
                    <select name="feed" onchange="this.form.submit()">
                        {"".join(feed_options)}
                    </select>
                    <label>
                        <input type="checkbox" name="unread" {unread_checked}
                               onchange="this.form.submit()"> Unread only
                    </label>
                    <button type="submit" style="margin-left: 0.5rem;">Search</button>
                </form>
                <form method="post" action="/mark-all-read" class="inline">
                    <button type="submit" class="btn-small">Mark all read</button>
                </form>
            </div>
            <table class="entries">
                <thead>
                    <tr><th>Date</th><th>Feed</th><th>Title</th></tr>
                </thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
            {_empty_message(rows, "No entries. Try fetching first.")}
        """)
        self._send_response(200, page_html)

    def _handle_entry(self, path: str) -> None:
        assert _conn is not None
        try:
            entry_id = int(path.split("/")[-1])
        except (ValueError, IndexError):
            self._send_response(400, "<h1>Bad request</h1>")
            return

        entry = database.get_entry(_conn, entry_id)
        if not entry:
            self._send_response(404, "<h1>Entry not found</h1>")
            return

        database.mark_read(_conn, entry_id)

        summary: str = entry["summary"] or "(no content)"
        if "<" in summary and ">" in summary:
            content = summary
        else:
            content = f"<p>{_esc(summary)}</p>"

        page_html = _page(_esc(entry["title"] or "Entry"), f"""
            <article>
                <h2>{_esc(entry["title"] or "(untitled)")}</h2>
                <div class="entry-meta">
                    <span>{_esc(entry["feed_title"] or "?")}</span>
                    <span>{(entry["published"] or "")[:16]}</span>
                    <a href="{_esc(entry["link"] or "#")}" target="_blank">Original</a>
                </div>
                <div class="entry-content">{content}</div>
            </article>
            <a href="/" class="back">&larr; Back to list</a>
        """)
        self._send_response(200, page_html)

    def _handle_feeds(self) -> None:
        assert _conn is not None
        feeds = database.list_feeds(_conn)

        rows: list[str] = []
        for f in feeds:
            title = _esc(f["title"] or "(untitled)")
            url = _esc(f["url"])
            fetched: str = f["last_fetched"] or "never"
            rows.append(f"""
                <tr>
                    <td>{f["id"]}</td>
                    <td>{title}</td>
                    <td class="url">{url}</td>
                    <td>{fetched}</td>
                    <td>
                        <form method="post" action="/remove/{f['id']}" class="inline">
                            <button type="submit" class="btn-danger">Remove</button>
                        </form>
                    </td>
                </tr>
            """)

        page_html = _page("Feeds", f"""
            <h2>Subscribed feeds</h2>
            <table class="feeds">
                <thead>
                    <tr><th>ID</th><th>Title</th><th>URL</th><th>Last fetched</th><th></th></tr>
                </thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
            {_empty_message(rows, "No feeds yet.")}

            <h3>Add feed</h3>
            <form method="post" action="/add" class="add-form">
                <input type="text" name="url" placeholder="Feed or website URL" required>
                <button type="submit">Add</button>
            </form>
        """)
        self._send_response(200, page_html)

    def _handle_stats(self) -> None:
        assert _conn is not None
        stats = database.get_stats(_conn)

        rows: list[str] = []
        total_entries = 0
        total_unread = 0
        for s in stats:
            title = _esc(s["title"] or s["url"])
            rows.append(f"""
                <tr>
                    <td>{title}</td>
                    <td>{s["total"]}</td>
                    <td>{s["unread"]}</td>
                    <td>{s["last_fetched"] or "never"}</td>
                </tr>
            """)
            total_entries += s["total"]
            total_unread += s["unread"]

        page_html = _page("Stats", f"""
            <h2>Statistics</h2>
            <div class="stats-summary">
                <span>Feeds: {len(stats)}</span>
                <span>Entries: {total_entries}</span>
                <span>Unread: {total_unread}</span>
            </div>
            <table class="stats">
                <thead>
                    <tr><th>Feed</th><th>Total</th><th>Unread</th><th>Last fetched</th></tr>
                </thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
        """)
        self._send_response(200, page_html)

    def _handle_add_feed(self, body: str) -> None:
        assert _conn is not None
        params = parse_qs(body)
        url = params.get("url", [""])[0].strip()

        if not url:
            self._redirect("/feeds")
            return

        from .discovery import discover_feeds

        try:
            feeds = discover_feeds(url)
        except Exception:
            feeds = [{"url": url, "title": None}]

        for feed in feeds:
            feed_url = feed.get("url")
            if feed_url:
                database.add_feed(_conn, feed_url, title=feed.get("title"))

        self._redirect("/feeds")

    def _handle_remove_feed(self, path: str) -> None:
        assert _conn is not None
        try:
            feed_id = int(path.split("/")[-1])
        except (ValueError, IndexError):
            self._send_response(400, "<h1>Bad request</h1>")
            return

        database.remove_feed(_conn, feed_id)
        self._redirect("/feeds")

    def _handle_mark_read(self, path: str) -> None:
        assert _conn is not None
        try:
            entry_id = int(path.split("/")[-1])
        except (ValueError, IndexError):
            self._send_response(400, "<h1>Bad request</h1>")
            return

        database.mark_read(_conn, entry_id)
        self._redirect("/")

    def _handle_mark_all_read(self) -> None:
        assert _conn is not None
        database.mark_all_read(_conn)
        self._redirect("/")

    def _handle_api(self, path: str, params: dict[str, list[str]]) -> None:
        assert _conn is not None
        if path == "/api/entries":
            entries = database.list_entries(_conn, limit=100)
            data: list[dict[str, Any]] = [dict(e) for e in entries]
            self._send_json(data)
        elif path == "/api/feeds":
            feeds = database.list_feeds(_conn)
            data = [dict(f) for f in feeds]
            self._send_json(data)
        else:
            self._send_json({"error": "not found"}, status=404)

    def _serve_css(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/css")
        self.end_headers()
        self.wfile.write(CSS.encode())

    def _send_response(self, status: int, html: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_json(self, data: Any, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


def serve(conn: sqlite3.Connection, host: str = "127.0.0.1", port: int = 8080) -> None:
    global _conn
    _conn = conn

    server = HTTPServer((host, port), FeedrHandler)
    print(f"Serving at http://{host}:{port}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def _esc(text: Any) -> str:
    return html_module.escape(str(text)) if text else ""


def _empty_message(rows: list[str], message: str) -> str:
    if not rows:
        return f'<p class="empty">{message}</p>'
    return ""


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} - rssmds</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <nav>
        <a href="/" class="logo">rssmds</a>
        <a href="/">Entries</a>
        <a href="/feeds">Feeds</a>
        <a href="/stats">Stats</a>
    </nav>
    <main>{body}</main>
</body>
</html>"""


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       background: #f8f9fa; color: #212529; line-height: 1.5; }
nav { background: #1a1a2e; padding: 0.75rem 1.5rem; display: flex; gap: 1.5rem; align-items: center; }
nav a { color: #e0e0e0; text-decoration: none; font-size: 0.9rem; }
nav a:hover { color: #fff; }
nav .logo { font-weight: bold; font-size: 1.1rem; color: #4fc3f7; margin-right: 1rem; }
main { max-width: 960px; margin: 1.5rem auto; padding: 0 1rem; }
h2 { margin-bottom: 1rem; }
h3 { margin: 1.5rem 0 0.75rem; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 4px;
        overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
thead { background: #e9ecef; }
th, td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #dee2e6; }
th { font-weight: 600; font-size: 0.85rem; text-transform: uppercase; color: #495057; }
tr.unread td { font-weight: 500; }
tr.read td { color: #6c757d; }
tr:hover { background: #f1f3f5; }
.entry-date { white-space: nowrap; font-size: 0.85rem; color: #868e96; width: 130px; }
.entry-feed { font-size: 0.85rem; color: #495057; width: 150px; }
.summary { font-size: 0.8rem; color: #868e96; margin-top: 2px; }
.url { font-size: 0.8rem; color: #868e96; word-break: break-all; }
.toolbar { display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;
           flex-wrap: wrap; }
.toolbar form { display: flex; gap: 0.5rem; align-items: center; }
.toolbar select, .toolbar input[type="text"] { padding: 0.35rem 0.5rem; border: 1px solid #ced4da;
    border-radius: 3px; font-size: 0.9rem; }
.toolbar label { font-size: 0.85rem; display: flex; align-items: center; gap: 0.3rem; }
button, .btn-small { padding: 0.35rem 0.75rem; border: none; border-radius: 3px;
    cursor: pointer; font-size: 0.85rem; background: #4fc3f7; color: #fff; }
button:hover { background: #039be5; }
.btn-danger { background: #e53935; }
.btn-danger:hover { background: #c62828; }
.btn-small { font-size: 0.8rem; padding: 0.25rem 0.5rem; }
.inline { display: inline; }
.add-form { display: flex; gap: 0.5rem; max-width: 500px; }
.add-form input { flex: 1; padding: 0.5rem; border: 1px solid #ced4da; border-radius: 3px; }
article { background: #fff; padding: 1.5rem; border-radius: 4px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.entry-meta { display: flex; gap: 1.5rem; color: #868e96; font-size: 0.9rem;
              margin: 0.5rem 0 1rem; padding-bottom: 1rem; border-bottom: 1px solid #dee2e6; }
.entry-meta a { color: #4fc3f7; }
.entry-content { line-height: 1.7; }
.entry-content img { max-width: 100%; }
.back { display: inline-block; margin-top: 1rem; color: #4fc3f7; text-decoration: none; }
.stats-summary { display: flex; gap: 2rem; margin-bottom: 1rem; font-size: 1.1rem; }
.empty { color: #868e96; padding: 2rem; text-align: center; }
"""

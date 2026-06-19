import argparse
import sqlite3
import sys
from typing import Any

from .config import load_config
from . import db
from .fetcher import fetch_all
from .discovery import discover_feeds
from .formatting import (
    format_entry_line,
    format_entry_detail,
    format_feed_list,
    format_stats,
    export_json,
    export_opml,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="rssmds",
        description="A terminal RSS/Atom feed reader.",
    )
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--db", help="Path to database file")

    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Subscribe to a feed")
    p_add.add_argument("url", help="Feed URL")
    p_add.add_argument("--title", help="Custom title for the feed")

    p_rm = sub.add_parser("remove", help="Unsubscribe from a feed")
    p_rm.add_argument("feed_id", type=int, help="Feed ID")

    sub.add_parser("feeds", help="List all subscribed feeds")

    sub.add_parser("fetch", help="Fetch new entries from all feeds")

    p_list = sub.add_parser("list", help="List entries")
    p_list.add_argument("--feed", type=int, help="Filter by feed ID")
    p_list.add_argument("--unread", action="store_true", help="Only show unread")
    p_list.add_argument("--limit", type=int, help="Max entries to show")

    p_read = sub.add_parser("read", help="Read an entry")
    p_read.add_argument("entry_id", type=int, help="Entry ID")

    p_mark = sub.add_parser("mark-read", help="Mark entries as read")
    p_mark.add_argument("--feed", type=int, help="Mark all in a feed as read")
    p_mark.add_argument("--all", action="store_true", dest="mark_all", help="Mark everything as read")

    sub.add_parser("stats", help="Show feed statistics")

    p_export = sub.add_parser("export", help="Export data")
    p_export.add_argument("format", choices=["json", "opml"], help="Export format")
    p_export.add_argument("--output", "-o", help="Output file (default: stdout)")

    p_discover = sub.add_parser("discover", help="Find RSS/Atom feeds on a website")
    p_discover.add_argument("url", help="Website URL to scan for feeds")
    p_discover.add_argument("--add", action="store_true", help="Automatically subscribe to discovered feeds")

    p_serve = sub.add_parser("serve", help="Start the web interface")
    p_serve.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")

    p_search = sub.add_parser("search", help="Search entry titles and summaries")
    p_search.add_argument("query", help="Search keyword")
    p_search.add_argument("--limit", type=int, help="Max entries to show")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config(args.config)
    db_path: str = args.db or config["db_path"]
    conn = db.connect(db_path)

    try:
        _dispatch(args, conn, config)
    finally:
        conn.close()


def _dispatch(args: argparse.Namespace, conn: sqlite3.Connection, config: dict[str, Any]) -> None:
    cmd = args.command

    if cmd == "add":
        _cmd_add(args, conn)
    elif cmd == "remove":
        _cmd_remove(args, conn)
    elif cmd == "feeds":
        _cmd_feeds(conn)
    elif cmd == "fetch":
        _cmd_fetch(conn, config)
    elif cmd == "list":
        _cmd_list(args, conn, config)
    elif cmd == "read":
        _cmd_read(args, conn)
    elif cmd == "mark-read":
        _cmd_mark_read(args, conn)
    elif cmd == "stats":
        _cmd_stats(conn)
    elif cmd == "export":
        _cmd_export(args, conn)
    elif cmd == "discover":
        _cmd_discover(args, conn)
    elif cmd == "serve":
        _cmd_serve(args, conn)
    elif cmd == "search":
        _cmd_search(args, conn, config)


def _cmd_add(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    ok = db.add_feed(conn, args.url, title=args.title)
    if ok:
        print(f"Added feed: {args.url}")
    else:
        print(f"Feed already exists: {args.url}", file=sys.stderr)
        sys.exit(1)


def _cmd_search(args: argparse.Namespace, conn: sqlite3.Connection, config: dict[str, Any]) -> None:
    limit: int = args.limit or config["max_entries_per_list"]
    entries = db.search_entries(conn, args.query, limit=limit)
    if not entries:
        print(f"No entries matching '{args.query}' found.")
        return
    for entry in entries:
        print(format_entry_line(entry))


def _cmd_remove(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    ok = db.remove_feed(conn, args.feed_id)
    if ok:
        print(f"Removed feed {args.feed_id}")
    else:
        print(f"Feed not found: {args.feed_id}", file=sys.stderr)
        sys.exit(1)


def _cmd_feeds(conn: sqlite3.Connection) -> None:
    feeds = db.list_feeds(conn)
    if not feeds:
        print("No feeds. Use 'rssmds add <url>' to subscribe.")
        return
    print(format_feed_list(feeds))


def _cmd_fetch(conn: sqlite3.Connection, config: dict[str, Any]) -> None:
    feeds = db.list_feeds(conn)
    if not feeds:
        print("No feeds to fetch. Use 'rssmds add <url>' to subscribe.")
        return

    results = fetch_all(conn, feeds, on_progress=lambda msg: print(msg))

    print()
    print(
        f"Done: {results['updated']} updated, "
        f"{results['unchanged']} unchanged, "
        f"{len(results['errors'])} errors"
    )
    for url, err in results["errors"]:
        print(f"  Error: {url}: {err}", file=sys.stderr)


def _cmd_list(args: argparse.Namespace, conn: sqlite3.Connection, config: dict[str, Any]) -> None:
    limit: int = args.limit or config["max_entries_per_list"]
    entries = db.list_entries(
        conn,
        feed_id=args.feed,
        unread_only=args.unread,
        limit=limit,
    )
    if not entries:
        print("No entries found.")
        return
    for entry in entries:
        print(format_entry_line(entry))


def _cmd_read(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    entry = db.get_entry(conn, args.entry_id)
    if not entry:
        print(f"Entry not found: {args.entry_id}", file=sys.stderr)
        sys.exit(1)
    db.mark_read(conn, args.entry_id)
    print(format_entry_detail(entry))


def _cmd_mark_read(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    if args.mark_all:
        db.mark_all_read(conn)
        print("Marked all entries as read.")
    elif args.feed is not None:
        db.mark_all_read(conn, feed_id=args.feed)
        print(f"Marked all entries in feed {args.feed} as read.")
    else:
        print("Specify --all or --feed <id>", file=sys.stderr)
        sys.exit(1)


def _cmd_stats(conn: sqlite3.Connection) -> None:
    stats = db.get_stats(conn)
    if not stats:
        print("No feeds.")
        return
    print(format_stats(stats))


def _cmd_discover(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    try:
        feeds = discover_feeds(args.url)
    except Exception as e:
        print(f"Error discovering feeds: {e}", file=sys.stderr)
        sys.exit(1)

    if not feeds:
        print("No feeds found.")
        return

    for feed in feeds:
        title = feed.get("title") or "(no title)"
        source = feed.get("source", "?")
        print(f"  [{source}] {feed['url']}  {title}")

    if args.add:
        added = 0
        for feed in feeds:
            feed_url = feed.get("url")
            if feed_url and db.add_feed(conn, feed_url, title=feed.get("title")):
                added += 1
        print(f"\nAdded {added} feed(s).")


def _cmd_serve(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    from .web import serve
    serve(conn, host=args.host, port=args.port)


def _cmd_export(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    output = ""
    if args.format == "json":
        entries = db.list_entries(conn, limit=10000)
        output = export_json(entries)
    elif args.format == "opml":
        feeds = db.list_feeds(conn)
        output = export_opml(feeds)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Exported to {args.output}", file=sys.stderr)
    else:
        print(output)

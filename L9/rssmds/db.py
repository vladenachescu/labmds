import sqlite3
from pathlib import Path
from datetime import datetime


def connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            etag TEXT,
            last_modified TEXT,
            last_fetched TEXT
        );
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
            guid TEXT NOT NULL,
            title TEXT,
            link TEXT,
            summary TEXT,
            published TEXT,
            read INTEGER DEFAULT 0,
            UNIQUE(feed_id, guid)
        );
        CREATE INDEX IF NOT EXISTS idx_entries_feed ON entries(feed_id);
        CREATE INDEX IF NOT EXISTS idx_entries_published ON entries(published);
    """)


def add_feed(conn: sqlite3.Connection, url: str, title: str | None = None) -> bool:
    try:
        conn.execute(
            "INSERT INTO feeds (url, title) VALUES (?, ?)",
            (url, title),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def remove_feed(conn: sqlite3.Connection, feed_id: int) -> bool:
    cursor = conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
    conn.commit()
    return cursor.rowcount > 0


def list_feeds(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, url, title, last_fetched FROM feeds ORDER BY id"
    ).fetchall()


def get_feed(conn: sqlite3.Connection, feed_id: int) -> sqlite3.Row | None:
    row: sqlite3.Row | None = conn.execute(
        "SELECT * FROM feeds WHERE id = ?", (feed_id,)
    ).fetchone()
    return row


def get_feed_by_url(conn: sqlite3.Connection, url: str) -> sqlite3.Row | None:
    row: sqlite3.Row | None = conn.execute(
        "SELECT * FROM feeds WHERE url = ?", (url,)
    ).fetchone()
    return row


def update_feed_meta(
    conn: sqlite3.Connection,
    feed_id: int,
    title: str | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
) -> None:
    now = datetime.now().isoformat()
    conn.execute(
        """UPDATE feeds
           SET title = COALESCE(?, title),
               etag = ?,
               last_modified = ?,
               last_fetched = ?
           WHERE id = ?""",
        (title, etag, last_modified, now, feed_id),
    )
    conn.commit()


def upsert_entry(
    conn: sqlite3.Connection,
    feed_id: int,
    guid: str,
    title: str,
    link: str,
    summary: str,
    published: str | None,
) -> bool:
    try:
        conn.execute(
            """INSERT INTO entries (feed_id, guid, title, link, summary, published)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed_id, guid, title, link, summary, published),
        )
        return True
    except sqlite3.IntegrityError:
        conn.execute(
            """UPDATE entries SET title=?, link=?, summary=?, published=?
               WHERE feed_id=? AND guid=?""",
            (title, link, summary, published, feed_id, guid),
        )
        return False


def list_entries(
    conn: sqlite3.Connection,
    feed_id: int | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> list[sqlite3.Row]:
    query = """
        SELECT e.id, e.title, e.link, e.summary, e.published, e.read,
               f.title as feed_title, f.id as feed_id
        FROM entries e
        JOIN feeds f ON e.feed_id = f.id
        WHERE 1=1
    """
    params: list[int] = []

    if feed_id is not None:
        query += " AND e.feed_id = ?"
        params.append(feed_id)
    if unread_only:
        query += " AND e.read = 0"

    query += " ORDER BY e.published DESC LIMIT ?"
    params.append(limit)

    return conn.execute(query, params).fetchall()


def get_entry(conn: sqlite3.Connection, entry_id: int) -> sqlite3.Row | None:
    row: sqlite3.Row | None = conn.execute(
        """SELECT e.*, f.title as feed_title
           FROM entries e JOIN feeds f ON e.feed_id = f.id
           WHERE e.id = ?""",
        (entry_id,),
    ).fetchone()
    return row


def mark_read(conn: sqlite3.Connection, entry_id: int) -> None:
    conn.execute("UPDATE entries SET read = 1 WHERE id = ?", (entry_id,))
    conn.commit()


def mark_all_read(conn: sqlite3.Connection, feed_id: int | None = None) -> None:
    if feed_id is not None:
        conn.execute("UPDATE entries SET read = 1 WHERE feed_id = ?", (feed_id,))
    else:
        conn.execute("UPDATE entries SET read = 1")
    conn.commit()


def get_stats(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute("""
        SELECT f.id, f.title, f.url, f.last_fetched,
               COUNT(e.id) as total,
               SUM(CASE WHEN e.read = 0 THEN 1 ELSE 0 END) as unread
        FROM feeds f
        LEFT JOIN entries e ON f.id = e.feed_id
        GROUP BY f.id
        ORDER BY unread DESC
    """).fetchall()
    return rows


def purge_entries(conn: sqlite3.Connection, older_than_date: str) -> int:
    cursor = conn.execute(
        "DELETE FROM entries WHERE published < ?",
        (older_than_date,),
    )
    conn.commit()
    return cursor.rowcount


def search_entries(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 50,
) -> list[sqlite3.Row]:
    sql_query = """
        SELECT e.id, e.title, e.link, e.summary, e.published, e.read,
               f.title as feed_title, f.id as feed_id
        FROM entries e
        JOIN feeds f ON e.feed_id = f.id
        WHERE e.title LIKE ? OR e.summary LIKE ?
        ORDER BY e.published DESC LIMIT ?
    """
    search_param = f"%{query}%"
    return conn.execute(sql_query, (search_param, search_param, limit)).fetchall()


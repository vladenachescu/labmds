import pytest
import threading
import time
import requests as http_requests

from rssmds import db
from rssmds.web import serve


@pytest.fixture
def server(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = db.connect(db_path)
    db.add_feed(conn, "https://example.com/feed.xml", title="Example Feed")
    db.upsert_entry(conn, 1, "guid-1", "Test Entry", "https://example.com/1",
                    "<p>Some <b>content</b></p>", "2025-01-06T12:00:00")
    db.upsert_entry(conn, 1, "guid-2", "Another Entry", "https://example.com/2",
                    "Plain text", "2025-01-05T12:00:00")
    conn.commit()

    from http.server import HTTPServer
    from rssmds.web import FeedrHandler, _conn
    import rssmds.web as web_module
    web_module._conn = conn

    srv = HTTPServer(("127.0.0.1", 0), FeedrHandler)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            http_requests.get(f"{base}/style.css", timeout=1)
            break
        except http_requests.ConnectionError:
            time.sleep(0.05)

    yield base, conn

    srv.shutdown()
    conn.close()


class TestWebIndex:
    def test_index_returns_200(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/")
        assert resp.status_code == 200
        assert "rssmds" in resp.text

    def test_index_shows_entries(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/")
        assert "Test Entry" in resp.text
        assert "Another Entry" in resp.text

    def test_index_filter_by_feed(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/?feed=1")
        assert resp.status_code == 200

    def test_index_unread_filter(self, server):
        base, conn = server
        db.mark_all_read(conn)
        resp = http_requests.get(f"{base}/?unread")
        assert "No entries" in resp.text


class TestWebEntry:
    def test_entry_page(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/entry/1")
        assert resp.status_code == 200
        assert "Test Entry" in resp.text

    def test_entry_marks_as_read(self, server):
        base, conn = server
        http_requests.get(f"{base}/entry/1")
        entry = db.get_entry(conn, 1)
        assert entry["read"] == 1

    def test_entry_not_found(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/entry/9999")
        assert resp.status_code == 404


class TestWebFeeds:
    def test_feeds_page(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/feeds")
        assert resp.status_code == 200
        assert "Example Feed" in resp.text


class TestWebStats:
    def test_stats_page(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/stats")
        assert resp.status_code == 200
        assert "Example Feed" in resp.text


class TestWebCSS:
    def test_css(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/style.css")
        assert resp.status_code == 200
        assert "text/css" in resp.headers["Content-Type"]


class TestWebAPI:
    def test_api_entries(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/api/entries")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_api_feeds(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/api/feeds")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_api_not_found(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/api/nope")
        assert resp.status_code == 404


class TestWebActions:
    def test_mark_all_read(self, server):
        base, conn = server
        http_requests.post(f"{base}/mark-all-read", allow_redirects=False)
        entries = db.list_entries(conn, unread_only=True)
        assert len(entries) == 0

    def test_remove_feed(self, server):
        base, conn = server
        http_requests.post(f"{base}/remove/1", allow_redirects=False)
        feeds = db.list_feeds(conn)
        assert len(feeds) == 0

    def test_404(self, server):
        base, _ = server
        resp = http_requests.get(f"{base}/nonexistent")
        assert resp.status_code == 404

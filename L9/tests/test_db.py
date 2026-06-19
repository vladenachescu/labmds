import pytest
from rssmds import db


@pytest.fixture
def conn(tmp_path):
    c = db.connect(str(tmp_path / "test.db"))
    yield c
    c.close()


@pytest.fixture
def populated(conn):
    db.add_feed(conn, "https://example.com/feed.xml", title="Example")
    db.add_feed(conn, "https://other.com/rss", title="Other")
    db.upsert_entry(conn, 1, "guid-1", "First Post", "https://example.com/1", "summary 1", "2025-01-01T00:00:00")
    db.upsert_entry(conn, 1, "guid-2", "Second Post", "https://example.com/2", "summary 2", "2025-01-02T00:00:00")
    db.upsert_entry(conn, 2, "guid-3", "Other Post", "https://other.com/1", "summary 3", "2025-01-03T00:00:00")
    conn.commit()
    return conn


class TestFeeds:
    def test_add_feed(self, conn):
        assert db.add_feed(conn, "https://example.com/feed.xml", title="Test")
        feeds = db.list_feeds(conn)
        assert len(feeds) == 1
        assert feeds[0]["url"] == "https://example.com/feed.xml"
        assert feeds[0]["title"] == "Test"

    def test_add_duplicate_feed(self, conn):
        db.add_feed(conn, "https://example.com/feed.xml")
        assert db.add_feed(conn, "https://example.com/feed.xml") is False

    def test_remove_feed(self, conn):
        db.add_feed(conn, "https://example.com/feed.xml")
        feeds = db.list_feeds(conn)
        assert db.remove_feed(conn, feeds[0]["id"])
        assert len(db.list_feeds(conn)) == 0

    def test_remove_nonexistent_feed(self, conn):
        assert db.remove_feed(conn, 9999) is False

    def test_remove_feed_cascades_entries(self, populated):
        entries_before = db.list_entries(populated, feed_id=1)
        assert len(entries_before) == 2
        db.remove_feed(populated, 1)
        entries_after = db.list_entries(populated, feed_id=1)
        assert len(entries_after) == 0

    def test_get_feed(self, conn):
        db.add_feed(conn, "https://example.com/feed.xml", title="Test")
        feed = db.get_feed(conn, 1)
        assert feed["url"] == "https://example.com/feed.xml"

    def test_get_feed_by_url(self, conn):
        db.add_feed(conn, "https://example.com/feed.xml", title="Test")
        feed = db.get_feed_by_url(conn, "https://example.com/feed.xml")
        assert feed is not None
        assert feed["title"] == "Test"

    def test_get_feed_by_url_missing(self, conn):
        assert db.get_feed_by_url(conn, "https://nope.com") is None

    def test_update_feed_meta(self, conn):
        db.add_feed(conn, "https://example.com/feed.xml")
        db.update_feed_meta(conn, 1, title="Updated", etag='"abc"', last_modified="Mon, 01 Jan 2025")
        feed = db.get_feed(conn, 1)
        assert feed["title"] == "Updated"
        assert feed["etag"] == '"abc"'
        assert feed["last_modified"] == "Mon, 01 Jan 2025"
        assert feed["last_fetched"] is not None


class TestEntries:
    def test_upsert_new_entry(self, conn):
        db.add_feed(conn, "https://example.com/feed.xml")
        result = db.upsert_entry(conn, 1, "guid-1", "Title", "https://link", "summary", "2025-01-01")
        conn.commit()
        assert result is True

    def test_upsert_existing_entry_updates(self, conn):
        db.add_feed(conn, "https://example.com/feed.xml")
        db.upsert_entry(conn, 1, "guid-1", "Title", "https://link", "summary", "2025-01-01")
        conn.commit()
        result = db.upsert_entry(conn, 1, "guid-1", "Updated Title", "https://link", "new summary", "2025-01-02")
        conn.commit()
        assert result is False
        entry = db.list_entries(conn, feed_id=1)[0]
        assert entry["title"] == "Updated Title"

    def test_list_entries_all(self, populated):
        entries = db.list_entries(populated)
        assert len(entries) == 3

    def test_list_entries_by_feed(self, populated):
        entries = db.list_entries(populated, feed_id=1)
        assert len(entries) == 2
        for e in entries:
            assert e["feed_id"] == 1

    def test_list_entries_unread_only(self, populated):
        db.mark_read(populated, 1)
        entries = db.list_entries(populated, unread_only=True)
        assert len(entries) == 2

    def test_list_entries_limit(self, populated):
        entries = db.list_entries(populated, limit=1)
        assert len(entries) == 1

    def test_list_entries_ordered_by_date_desc(self, populated):
        entries = db.list_entries(populated)
        dates = [e["published"] for e in entries]
        assert dates == sorted(dates, reverse=True)

    def test_get_entry(self, populated):
        entry = db.get_entry(populated, 1)
        assert entry is not None
        assert entry["title"] == "First Post"
        assert entry["feed_title"] == "Example"

    def test_get_entry_missing(self, populated):
        assert db.get_entry(populated, 9999) is None

    def test_mark_read(self, populated):
        db.mark_read(populated, 1)
        entry = db.get_entry(populated, 1)
        assert entry["read"] == 1

    def test_mark_all_read(self, populated):
        db.mark_all_read(populated)
        entries = db.list_entries(populated, unread_only=True)
        assert len(entries) == 0

    def test_mark_all_read_by_feed(self, populated):
        db.mark_all_read(populated, feed_id=1)
        feed1 = db.list_entries(populated, feed_id=1, unread_only=True)
        feed2 = db.list_entries(populated, feed_id=2, unread_only=True)
        assert len(feed1) == 0
        assert len(feed2) == 1


class TestStats:
    def test_stats(self, populated):
        stats = db.get_stats(populated)
        assert len(stats) == 2
        example = [s for s in stats if s["title"] == "Example"][0]
        assert example["total"] == 2
        assert example["unread"] == 2

    def test_stats_empty(self, conn):
        assert db.get_stats(conn) == []


class TestPurge:
    def test_purge_old_entries(self, populated):
        removed = db.purge_entries(populated, "2025-01-02T00:00:00")
        assert removed == 1
        entries = db.list_entries(populated)
        assert len(entries) == 2

    def test_purge_nothing(self, populated):
        removed = db.purge_entries(populated, "2020-01-01")
        assert removed == 0


class TestSearch:
    def test_search_by_title(self, populated):
        results = db.search_entries(populated, "First")
        assert len(results) == 1
        assert results[0]["title"] == "First Post"

    def test_search_by_summary(self, populated):
        results = db.search_entries(populated, "summary 3")
        assert len(results) == 1
        assert results[0]["title"] == "Other Post"

    def test_search_no_results(self, populated):
        results = db.search_entries(populated, "nonexistent")
        assert len(results) == 0


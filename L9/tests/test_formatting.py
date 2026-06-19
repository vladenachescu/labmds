from rssmds.formatting import (
    format_entry_line,
    format_entry_detail,
    format_feed_list,
    format_stats,
    export_json,
    export_opml,
    _strip_html,
)

import json


def _make_entry(**overrides):
    entry = {
        "id": 1,
        "title": "Test Entry",
        "link": "https://example.com/1",
        "summary": "A summary",
        "published": "2025-01-06T12:00:00",
        "read": 0,
        "feed_title": "Test Feed",
        "feed_id": 1,
    }
    entry.update(overrides)
    return entry


def _make_feed(**overrides):
    feed = {
        "id": 1,
        "url": "https://example.com/feed.xml",
        "title": "Test Feed",
        "last_fetched": "2025-01-06T12:00:00",
    }
    feed.update(overrides)
    return feed


class TestEntryLine:
    def test_unread_marker(self):
        line = format_entry_line(_make_entry(read=0))
        assert line.startswith("*")

    def test_read_marker(self):
        line = format_entry_line(_make_entry(read=1))
        assert line.startswith(" ")

    def test_contains_title(self):
        line = format_entry_line(_make_entry(title="My Title"))
        assert "My Title" in line

    def test_contains_feed_title(self):
        line = format_entry_line(_make_entry(feed_title="My Feed"))
        assert "My Feed" in line

    def test_truncates_long_title(self):
        line = format_entry_line(_make_entry(title="A" * 200), width=80)
        assert len(line) <= 85

    def test_no_published_date(self):
        line = format_entry_line(_make_entry(published=None))
        assert "[1]" in line


class TestEntryDetail:
    def test_contains_fields(self):
        detail = format_entry_detail(_make_entry())
        assert "Test Entry" in detail
        assert "Test Feed" in detail
        assert "https://example.com/1" in detail

    def test_strips_html_from_summary(self):
        detail = format_entry_detail(_make_entry(summary="<p>Hello <b>world</b></p>"))
        assert "Hello world" in detail
        assert "<p>" not in detail

    def test_no_summary(self):
        detail = format_entry_detail(_make_entry(summary=None))
        assert "(no summary)" in detail


class TestFeedList:
    def test_shows_feed_info(self):
        output = format_feed_list([_make_feed()])
        assert "Test Feed" in output
        assert "https://example.com/feed.xml" in output

    def test_shows_never_fetched(self):
        output = format_feed_list([_make_feed(last_fetched=None)])
        assert "never" in output


class TestStats:
    def _make_stat(self, **overrides):
        stat = {
            "id": 1, "title": "Feed", "url": "https://example.com",
            "last_fetched": "2025-01-06", "total": 10, "unread": 3,
        }
        stat.update(overrides)
        return stat

    def test_shows_totals(self):
        output = format_stats([self._make_stat(total=10, unread=3)])
        assert "Entries: 10" in output
        assert "Unread: 3" in output

    def test_multiple_feeds(self):
        output = format_stats([
            self._make_stat(title="A", total=5, unread=2),
            self._make_stat(title="B", total=3, unread=1),
        ])
        assert "Entries: 8" in output
        assert "Unread: 3" in output


class TestExport:
    def test_json_export(self):
        entries = [_make_entry(), _make_entry(id=2, title="Second")]
        output = export_json(entries)
        data = json.loads(output)
        assert len(data) == 2
        assert data[0]["title"] == "Test Entry"

    def test_opml_export(self):
        feeds = [_make_feed()]
        output = export_opml(feeds)
        assert "<?xml" in output
        assert "<opml" in output
        assert "example.com/feed.xml" in output
        assert "Test Feed" in output


class TestStripHtml:
    def test_removes_tags(self):
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_converts_br(self):
        assert "\n" in _strip_html("line1<br>line2")

    def test_unescapes_entities(self):
        assert _strip_html("&amp; &lt; &gt;") == "& < >"

    def test_empty(self):
        assert _strip_html("") == ""

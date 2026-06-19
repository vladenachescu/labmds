import pytest
from rssmds.parser import parse_feed, _parse_date


RSS_MINIMAL = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>First</title>
      <link>https://example.com/1</link>
      <guid>https://example.com/1</guid>
      <description>Hello world</description>
      <pubDate>Mon, 06 Jan 2025 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second</title>
      <link>https://example.com/2</link>
      <guid>https://example.com/2</guid>
    </item>
  </channel>
</rss>
"""

ATOM_MINIMAL = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Feed</title>
  <entry>
    <id>urn:uuid:1</id>
    <title>Atom Entry</title>
    <link rel="alternate" href="https://example.com/atom/1"/>
    <summary>Atom summary</summary>
    <updated>2025-01-06T12:00:00Z</updated>
  </entry>
</feed>
"""

ATOM_NO_NS = """<?xml version="1.0"?>
<feed>
  <title>No Namespace</title>
  <entry>
    <id>1</id>
    <title>Entry</title>
    <link href="https://example.com/1"/>
    <content>Some content</content>
    <published>2025-03-15T10:30:00Z</published>
  </entry>
</feed>
"""

RSS_NO_GUID = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>No GUID Feed</title>
    <item>
      <title>No GUID</title>
      <link>https://example.com/no-guid</link>
      <description>Falls back to link as guid</description>
    </item>
    <item>
      <title>No GUID or Link</title>
      <description>Should be skipped</description>
    </item>
  </channel>
</rss>
"""


class TestRSS:
    def test_parse_rss_title(self):
        title, entries = parse_feed(RSS_MINIMAL)
        assert title == "Test Feed"

    def test_parse_rss_entries(self):
        title, entries = parse_feed(RSS_MINIMAL)
        assert len(entries) == 2

    def test_parse_rss_entry_fields(self):
        _, entries = parse_feed(RSS_MINIMAL)
        first = entries[0]
        assert first["title"] == "First"
        assert first["link"] == "https://example.com/1"
        assert first["guid"] == "https://example.com/1"
        assert first["summary"] == "Hello world"
        assert first["published"] is not None

    def test_parse_rss_missing_description(self):
        _, entries = parse_feed(RSS_MINIMAL)
        second = entries[1]
        assert second["summary"] == ""

    def test_parse_rss_no_guid_falls_back_to_link(self):
        _, entries = parse_feed(RSS_NO_GUID)
        assert len(entries) == 1
        assert entries[0]["guid"] == "https://example.com/no-guid"


class TestAtom:
    def test_parse_atom_title(self):
        title, entries = parse_feed(ATOM_MINIMAL)
        assert title == "Atom Feed"

    def test_parse_atom_entry(self):
        _, entries = parse_feed(ATOM_MINIMAL)
        assert len(entries) == 1
        entry = entries[0]
        assert entry["title"] == "Atom Entry"
        assert entry["link"] == "https://example.com/atom/1"
        assert entry["summary"] == "Atom summary"

    def test_parse_atom_no_namespace(self):
        title, entries = parse_feed(ATOM_NO_NS)
        assert title == "No Namespace"
        assert len(entries) == 1
        assert entries[0]["link"] == "https://example.com/1"

    def test_parse_atom_content_as_summary(self):
        _, entries = parse_feed(ATOM_NO_NS)
        assert entries[0]["summary"] == "Some content"


class TestDateParsing:
    def test_rfc2822(self):
        result = _parse_date("Mon, 06 Jan 2025 12:00:00 GMT")
        assert "2025-01-06" in result

    def test_iso8601_with_z(self):
        result = _parse_date("2025-01-06T12:00:00Z")
        assert "2025-01-06" in result

    def test_iso8601_with_tz(self):
        result = _parse_date("2025-01-06T12:00:00+02:00")
        assert "2025-01-06" in result

    def test_date_only(self):
        result = _parse_date("2025-01-06")
        assert "2025-01-06" in result

    def test_none(self):
        assert _parse_date(None) is None

    def test_empty(self):
        assert _parse_date("") is None

    def test_garbage_returned_as_is(self):
        assert _parse_date("not a date") == "not a date"


class TestUnknownFormat:
    def test_unknown_root_tag(self):
        with pytest.raises(ValueError, match="Unknown feed format"):
            parse_feed('<?xml version="1.0"?><html></html>')

    def test_rss_missing_channel(self):
        with pytest.raises(ValueError, match="missing <channel>"):
            parse_feed('<?xml version="1.0"?><rss version="2.0"></rss>')

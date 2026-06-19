import pytest
from rssmds.discovery import (
    _extract_link_tags,
    _extract_anchor_links,
    _looks_like_xml_feed,
    _is_feed_content_type,
)


HTML_WITH_FEED_LINKS = """
<html>
<head>
    <link rel="alternate" type="application/rss+xml" title="RSS" href="/feed.xml">
    <link rel="alternate" type="application/atom+xml" title="Atom" href="https://example.com/atom.xml">
    <link rel="stylesheet" href="/style.css">
</head>
<body></body>
</html>
"""

HTML_WITH_ANCHOR_FEEDS = """
<html>
<body>
    <a href="/blog/feed.xml">RSS Feed</a>
    <a href="/about">About</a>
    <a href="https://example.com/rss.xml">Subscribe via RSS</a>
    <a href="/podcast.rss">Podcast</a>
</body>
</html>
"""

HTML_NO_FEEDS = """
<html>
<head><title>No feeds</title></head>
<body><p>Nothing here.</p></body>
</html>
"""


class TestLinkTagExtraction:
    def test_finds_rss_link(self):
        feeds = _extract_link_tags(HTML_WITH_FEED_LINKS, "https://example.com")
        urls = [f["url"] for f in feeds]
        assert "https://example.com/feed.xml" in urls

    def test_finds_atom_link(self):
        feeds = _extract_link_tags(HTML_WITH_FEED_LINKS, "https://example.com")
        urls = [f["url"] for f in feeds]
        assert "https://example.com/atom.xml" in urls

    def test_ignores_stylesheet(self):
        feeds = _extract_link_tags(HTML_WITH_FEED_LINKS, "https://example.com")
        urls = [f["url"] for f in feeds]
        assert not any("style.css" in u for u in urls)

    def test_extracts_title(self):
        feeds = _extract_link_tags(HTML_WITH_FEED_LINKS, "https://example.com")
        titles = {f["title"] for f in feeds}
        assert "RSS" in titles
        assert "Atom" in titles

    def test_resolves_relative_urls(self):
        feeds = _extract_link_tags(HTML_WITH_FEED_LINKS, "https://example.com/blog/")
        urls = [f["url"] for f in feeds]
        assert any(u.startswith("https://example.com") for u in urls)

    def test_no_feeds(self):
        feeds = _extract_link_tags(HTML_NO_FEEDS, "https://example.com")
        assert feeds == []


class TestAnchorExtraction:
    def test_finds_xml_links(self):
        feeds = _extract_anchor_links(HTML_WITH_ANCHOR_FEEDS, "https://example.com")
        urls = [f["url"] for f in feeds]
        assert any("feed.xml" in u for u in urls)
        assert any("rss.xml" in u for u in urls)

    def test_finds_rss_extension(self):
        feeds = _extract_anchor_links(HTML_WITH_ANCHOR_FEEDS, "https://example.com")
        urls = [f["url"] for f in feeds]
        assert any("podcast.rss" in u for u in urls)

    def test_ignores_regular_links(self):
        feeds = _extract_anchor_links(HTML_WITH_ANCHOR_FEEDS, "https://example.com")
        urls = [f["url"] for f in feeds]
        assert not any("about" in u for u in urls)

    def test_no_duplicates(self):
        html = """
        <html><body>
            <a href="/feed.xml">Feed 1</a>
            <a href="/feed.xml">Feed 2</a>
        </body></html>
        """
        feeds = _extract_anchor_links(html, "https://example.com")
        assert len(feeds) == 1


class TestHelpers:
    def test_is_feed_content_type(self):
        assert _is_feed_content_type("application/rss+xml")
        assert _is_feed_content_type("application/atom+xml; charset=utf-8")
        assert _is_feed_content_type("application/xml")
        assert not _is_feed_content_type("text/html")
        assert not _is_feed_content_type("application/json")

    def test_looks_like_xml_feed_rss(self):
        assert _looks_like_xml_feed('<?xml version="1.0"?><rss version="2.0">')

    def test_looks_like_xml_feed_atom(self):
        assert _looks_like_xml_feed('<?xml version="1.0"?><feed xmlns="...">')

    def test_not_a_feed(self):
        assert not _looks_like_xml_feed("<html><body>hello</body></html>")
        assert not _looks_like_xml_feed('<?xml version="1.0"?><svg></svg>')

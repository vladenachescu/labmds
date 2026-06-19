from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .fetcher import USER_AGENT, DEFAULT_TIMEOUT


FEED_MIME_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
}

COMMON_FEED_PATHS = [
    "/feed",
    "/feed.xml",
    "/rss",
    "/rss.xml",
    "/atom.xml",
    "/index.xml",
    "/feeds/posts/default",
]

FeedInfo = dict[str, str | None]


def discover_feeds(url: str, timeout: int = DEFAULT_TIMEOUT) -> list[FeedInfo]:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if _is_feed_content_type(content_type):
        return [{"url": url, "title": None, "source": "direct"}]

    if _looks_like_xml_feed(response.text):
        return [{"url": url, "title": None, "source": "direct"}]

    feeds = _extract_link_tags(response.text, url)
    if feeds:
        return feeds

    feeds = _probe_common_paths(url, timeout)
    if feeds:
        return feeds

    feeds = _extract_anchor_links(response.text, url)
    return feeds


def _is_feed_content_type(content_type: str) -> bool:
    ct = content_type.split(";")[0].strip().lower()
    return ct in FEED_MIME_TYPES


def _looks_like_xml_feed(text: str) -> bool:
    stripped = text.lstrip()[:500]
    if "<?xml" in stripped:
        if "<rss" in stripped or "<feed" in stripped or "<rdf" in stripped:
            return True
    return False


def _extract_link_tags(html_text: str, base_url: str) -> list[FeedInfo]:
    soup = BeautifulSoup(html_text, "html.parser")
    feeds: list[FeedInfo] = []

    for link in soup.find_all("link", rel="alternate"):
        link_type = (link.get("type") or "").lower()
        if link_type not in FEED_MIME_TYPES:
            continue

        href = link.get("href")
        if not href:
            continue

        feed_url = urljoin(base_url, href)
        title = link.get("title")
        feeds.append({"url": feed_url, "title": title, "source": "link_tag"})

    return feeds


def _probe_common_paths(url: str, timeout: int) -> list[FeedInfo]:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    feeds: list[FeedInfo] = []
    for path in COMMON_FEED_PATHS:
        probe_url = base + path
        try:
            resp = requests.head(
                probe_url,
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
                allow_redirects=True,
            )
            if resp.status_code == 200:
                ct = resp.headers.get("Content-Type", "")
                if _is_feed_content_type(ct):
                    feeds.append({
                        "url": probe_url,
                        "title": None,
                        "source": "probe",
                    })
        except requests.RequestException:
            continue

    return feeds


def _extract_anchor_links(html_text: str, base_url: str) -> list[FeedInfo]:
    soup = BeautifulSoup(html_text, "html.parser")
    feeds: list[FeedInfo] = []
    seen: set[str] = set()

    feed_keywords = {"rss", "feed", "atom", "xml"}

    for a in soup.find_all("a", href=True):
        href: str = a["href"].lower()
        text: str = (a.get_text() or "").lower()

        if any(kw in href or kw in text for kw in feed_keywords):
            full_url = urljoin(base_url, a["href"])
            if full_url in seen:
                continue
            seen.add(full_url)

            if any(full_url.endswith(ext) for ext in [".xml", ".rss", ".atom"]):
                feeds.append({
                    "url": full_url,
                    "title": a.get_text().strip() or None,
                    "source": "anchor",
                })

    return feeds

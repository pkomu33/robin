"""Limited recursive crawler for Robin V1.1.

This module intentionally stays small. It builds on scrape.fetch_page_for_crawl
and does not replace the legacy scrape_single()/scrape_multiple() workflow.
"""

from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

from scrape import fetch_page_for_crawl


def _normalize_http_url(base_url, href):
    """Resolve an href and return a fragment-free HTTP(S) URL, else None."""
    if not isinstance(href, str):
        return None
    href = href.strip()
    if not href:
        return None

    try:
        resolved = urljoin(base_url, href)
        resolved, _fragment = urldefrag(resolved)
        parsed = urlparse(resolved)
    except (TypeError, ValueError):
        return None

    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if not parsed.hostname:
        return None
    return resolved


def _seed_item(seed):
    if isinstance(seed, str):
        return seed.strip(), "Untitled"
    if isinstance(seed, dict):
        url = str(seed.get("link") or "").strip()
        title = str(seed.get("title") or "Untitled").strip() or "Untitled"
        return url, title
    return "", "Untitled"


def crawl(urls_data, max_depth=0, max_pages=10, same_host=True):
    """Crawl seed URLs breadth-first with strict page/depth bounds.

    Args:
        urls_data: iterable of V0-style {"link", "title"} dicts or URL strings.
        max_depth: 0 fetches only seeds; 1 also fetches their children, etc.
        max_pages: maximum number of unique URLs attempted in the whole crawl.
        same_host: when True, only links whose hostname matches their seed
            hostname are followed.

    Returns:
        A list of page records. Each record includes url, parent_url,
        crawl_depth, title and content.
    """
    try:
        max_depth = int(max_depth)
        max_pages = int(max_pages)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_depth and max_pages must be integers") from exc

    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    if max_pages <= 0:
        return []
    if not isinstance(urls_data, (list, tuple)):
        return []

    queue = deque()
    for seed in urls_data:
        seed_url, seed_title = _seed_item(seed)
        normalized = _normalize_http_url(seed_url, seed_url)
        if not normalized:
            continue
        root_host = (urlparse(normalized).hostname or "").lower()
        queue.append((normalized, seed_title, None, 0, root_host))

    visited = set()
    pages = []
    attempts = 0

    while queue and attempts < max_pages:
        url, title, parent_url, depth, root_host = queue.popleft()
        if url in visited:
            continue

        visited.add(url)
        attempts += 1

        fetched = fetch_page_for_crawl({"link": url, "title": title})
        if fetched is None:
            continue

        pages.append(
            {
                "url": fetched["url"],
                "parent_url": parent_url,
                "crawl_depth": depth,
                "title": fetched["title"],
                "content": fetched["content"],
            }
        )

        if depth >= max_depth:
            continue

        for href in fetched.get("links", []):
            child_url = _normalize_http_url(url, href)
            if not child_url or child_url in visited:
                continue

            child_host = (urlparse(child_url).hostname or "").lower()
            if same_host and child_host != root_host:
                continue

            queue.append((child_url, "Untitled", url, depth + 1, root_host))

    return pages

"""Portable investigation exporters for Robin V1.4.

The exporters operate on the investigation dictionaries already produced by
V1.3. They do not change search, crawling, entity extraction, or LLM behavior.
"""

import csv
import io
import json
from pathlib import Path


CSV_COLUMNS = [
    "url",
    "parent_url",
    "crawl_depth",
    "timestamp",
    "title",
    "normalized_text",
    "onion_urls",
    "emails",
    "domains",
    "ips",
    "hashes",
    "cves",
    "handles",
]


def _stable_values(*groups):
    """Return de-duplicated strings in deterministic first-seen order."""
    seen = set()
    values = []
    for group in groups:
        if not isinstance(group, (list, tuple, set)):
            continue
        iterable = sorted(group, key=lambda value: str(value)) if isinstance(group, set) else group
        for value in iterable:
            value = str(value)
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return values


def _page_entities(page):
    entities = page.get("entities") or {}
    if not isinstance(entities, dict):
        entities = {}
    return {
        "onion_urls": _stable_values(entities.get("onion_urls", [])),
        "emails": _stable_values(entities.get("emails", [])),
        "domains": _stable_values(entities.get("domains", [])),
        "ips": _stable_values(
            entities.get("ips", []),
            entities.get("ipv4", []),
            entities.get("ipv6", []),
        ),
        "hashes": _stable_values(
            entities.get("hashes", []),
            entities.get("md5", []),
            entities.get("sha1", []),
            entities.get("sha256", []),
        ),
        "cves": _stable_values(entities.get("cves", [])),
        "handles": _stable_values(entities.get("handles", [])),
    }


def investigation_to_json(investigation):
    """Serialize the full investigation structure as UTF-8 JSON text."""
    return json.dumps(investigation, indent=2, ensure_ascii=False)


def investigation_to_csv(investigation):
    """Serialize one CSV row per crawled page; legacy V0 yields header only."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()

    pages = investigation.get("pages", []) or []
    if not isinstance(pages, list):
        pages = []

    for page in pages:
        if not isinstance(page, dict):
            continue
        entities = _page_entities(page)
        writer.writerow(
            {
                "url": page.get("url", ""),
                "parent_url": page.get("parent_url") or "",
                "crawl_depth": page.get("crawl_depth", ""),
                "timestamp": page.get("timestamp", ""),
                "title": page.get("title", ""),
                "normalized_text": page.get("normalized_text", page.get("content", "")),
                "onion_urls": ";".join(entities["onion_urls"]),
                "emails": ";".join(entities["emails"]),
                "domains": ";".join(entities["domains"]),
                "ips": ";".join(entities["ips"]),
                "hashes": ";".join(entities["hashes"]),
                "cves": ";".join(entities["cves"]),
                "handles": ";".join(entities["handles"]),
            }
        )

    return output.getvalue()


def _aggregate_entities(pages):
    aggregate = {key: [] for key in ("onion_urls", "emails", "domains", "ips", "hashes", "cves", "handles")}
    seen = {key: set() for key in aggregate}

    for page in pages:
        if not isinstance(page, dict):
            continue
        grouped = _page_entities(page)
        for key, values in grouped.items():
            for value in values:
                if value not in seen[key]:
                    seen[key].add(value)
                    aggregate[key].append(value)
    return aggregate


def investigation_to_markdown(investigation):
    """Render a concise human-readable Markdown investigation report."""
    pages = investigation.get("pages", []) or []
    if not isinstance(pages, list):
        pages = []
    crawl = investigation.get("crawl") or {}
    if not isinstance(crawl, dict):
        crawl = {}

    lines = [
        "# Robin Investigation",
        "",
        f"**Query:** {investigation.get('query', '')}",
        "",
        f"**Refined Query:** {investigation.get('refined_query', '')}",
        "",
        f"**Model:** {investigation.get('model', '')}",
        "",
        f"**Preset:** {investigation.get('preset', '')}",
        "",
        f"**Timestamp:** {investigation.get('timestamp', '')}",
        "",
        "**Crawler configuration:**",
    ]

    if crawl:
        for key in ("max_depth", "max_pages", "scope"):
            if key in crawl:
                lines.append(f"- {key}: {crawl[key]}")
        for key in sorted(k for k in crawl if k not in {"max_depth", "max_pages", "scope"}):
            lines.append(f"- {key}: {crawl[key]}")
    else:
        lines.append("- Not available (legacy investigation)")

    lines.extend(["", "## Findings", "", investigation.get("summary", "") or "_No summary._", "", "## Crawled Sources", ""])

    if pages:
        for index, page in enumerate(pages, 1):
            if not isinstance(page, dict):
                continue
            parent = page.get("parent_url") or "root"
            lines.append(
                f"{index}. {page.get('title', 'Untitled')} — {page.get('url', '')} "
                f"(depth={page.get('crawl_depth', '')}, parent={parent})"
            )
    else:
        lines.append("_No crawled page records are stored in this investigation._")

    lines.extend(["", "## Extracted Entities", ""])
    aggregate = _aggregate_entities(pages)
    labels = {
        "onion_urls": "Onion URLs",
        "emails": "Emails",
        "domains": "Domains",
        "ips": "IPs",
        "hashes": "Hashes",
        "cves": "CVEs",
        "handles": "Handles",
    }
    any_entities = False
    for key in ("onion_urls", "emails", "domains", "ips", "hashes", "cves", "handles"):
        values = aggregate[key]
        if not values:
            continue
        any_entities = True
        lines.append(f"### {labels[key]}")
        lines.extend(f"- {value}" for value in values)
        lines.append("")

    if not any_entities:
        lines.append("_No extracted entities are stored in this investigation._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_investigation_exports(investigation, output_dir, stem="investigation"):
    """Write JSON, CSV and Markdown files and return their Path objects."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "json": output_dir / f"{stem}.json",
        "csv": output_dir / f"{stem}.csv",
        "markdown": output_dir / f"{stem}.md",
    }
    paths["json"].write_text(investigation_to_json(investigation), encoding="utf-8")
    paths["csv"].write_text(investigation_to_csv(investigation), encoding="utf-8", newline="")
    paths["markdown"].write_text(investigation_to_markdown(investigation), encoding="utf-8")
    return paths

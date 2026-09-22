#!/usr/bin/env python3
"""Offline export test for Robin V1.4."""

import csv
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from exporters import (  # noqa: E402
    investigation_to_csv,
    investigation_to_json,
    investigation_to_markdown,
    write_investigation_exports,
)


def _v1_record():
    return {
        "timestamp": "2026-09-22T20:01:00",
        "query": "controlled query",
        "refined_query": "controlled refined query",
        "model": "test-model",
        "preset": "test-preset",
        "crawl": {"max_depth": 1, "max_pages": 20, "scope": "same_host"},
        "sources": [{"link": "http://example.test/root", "title": "Root"}],
        "pages": [
            {
                "url": "http://example.test/root",
                "parent_url": None,
                "crawl_depth": 0,
                "timestamp": "2026-09-22T20:00:00Z",
                "title": "Root",
                "normalized_text": "root normalized text",
                "entities": {
                    "onion_urls": ["http://aaaaaaaaaaaaaaaa.onion/"],
                    "emails": ["analyst@example.com"],
                    "domains": ["example.com"],
                    "ipv4": ["192.0.2.10"],
                    "ipv6": ["2001:db8::5"],
                    "md5": ["d41d8cd98f00b204e9800998ecf8427e"],
                    "sha1": ["da39a3ee5e6b4b0d3255bfef95601890afd80709"],
                    "sha256": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
                    "cves": ["CVE-2024-12345"],
                    "handles": ["@researcher_01"],
                },
            },
            {
                "url": "http://example.test/child",
                "parent_url": "http://example.test/root",
                "crawl_depth": 1,
                "timestamp": "2026-09-22T20:00:01Z",
                "title": "Child",
                "normalized_text": "child normalized text",
                "entities": {
                    "onion_urls": [],
                    "emails": ["analyst@example.com"],
                    "domains": ["child.example.org"],
                    "ipv4": [],
                    "ipv6": [],
                    "md5": [],
                    "sha1": [],
                    "sha256": [],
                    "cves": [],
                    "handles": [],
                },
            },
        ],
        "summary": "controlled summary",
    }


def _legacy_record():
    return {
        "timestamp": "2026-01-01T10:00:00",
        "query": "legacy query",
        "refined_query": "legacy refined",
        "model": "legacy-model",
        "preset": "legacy-preset",
        "sources": [{"link": "http://legacy.example", "title": "Legacy"}],
        "summary": "legacy summary",
    }


def main():
    v1 = _v1_record()

    json_text = investigation_to_json(v1)
    decoded = json.loads(json_text)
    assert decoded["query"] == "controlled query"
    assert decoded["crawl"]["max_depth"] == 1
    assert decoded["pages"][0]["entities"]["cves"] == ["CVE-2024-12345"]

    csv_text = investigation_to_csv(v1)
    rows = list(csv.DictReader(csv_text.splitlines()))
    assert len(rows) == 2
    assert rows[0]["parent_url"] == ""
    assert rows[1]["parent_url"] == "http://example.test/root"
    assert rows[1]["crawl_depth"] == "1"
    assert rows[0]["ips"] == "192.0.2.10;2001:db8::5"
    assert rows[0]["hashes"].startswith("d41d8cd98f00b204e9800998ecf8427e;")
    assert rows[0]["cves"] == "CVE-2024-12345"
    assert rows[0]["handles"] == "@researcher_01"

    md_text = investigation_to_markdown(v1)
    for required in (
        "# Robin Investigation",
        "**Query:** controlled query",
        "**Refined Query:** controlled refined query",
        "**Model:** test-model",
        "**Timestamp:** 2026-09-22T20:01:00",
        "## Findings",
        "controlled summary",
        "## Crawled Sources",
        "depth=1, parent=http://example.test/root",
        "## Extracted Entities",
        "### CVEs",
        "- CVE-2024-12345",
    ):
        assert required in md_text, required

    legacy = _legacy_record()
    legacy_json = json.loads(investigation_to_json(legacy))
    assert legacy_json["query"] == "legacy query"
    legacy_rows = list(csv.DictReader(investigation_to_csv(legacy).splitlines()))
    assert legacy_rows == []
    legacy_md = investigation_to_markdown(legacy)
    assert "legacy summary" in legacy_md
    assert "Not available (legacy investigation)" in legacy_md
    assert "No crawled page records" in legacy_md

    with tempfile.TemporaryDirectory(prefix="robin-v1-export-") as temp_dir:
        paths = write_investigation_exports(v1, temp_dir, stem="sample")
        assert all(path.exists() for path in paths.values())
        assert json.loads(paths["json"].read_text(encoding="utf-8"))["query"] == "controlled query"
        assert "url,parent_url,crawl_depth" in paths["csv"].read_text(encoding="utf-8")
        assert "# Robin Investigation" in paths["markdown"].read_text(encoding="utf-8")

    print("PASS: V1 investigation exports full JSON structure")
    print("PASS: CSV writes one row per crawled page with deterministic entity fields")
    print("PASS: Markdown contains metadata, findings, crawled sources and aggregated entities")
    print("PASS: export files are written as JSON, CSV and Markdown")
    print("PASS: legacy V0 investigation exports without pages/crawl and does not fail")
    print("PASS: export test requires no Tor, Internet, Streamlit or LLM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline persistence test for Robin V1.3."""

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from investigation import (  # noqa: E402
    build_investigation_record,
    load_investigations,
    save_investigation,
)


def main():
    entities = {
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
    }
    pages = [
        {
            "url": "http://example.test/root",
            "parent_url": None,
            "crawl_depth": 0,
            "timestamp": "2026-09-22T20:00:00Z",
            "title": "Root",
            "normalized_text": "root normalized text",
            "entities": entities,
            "content": "root normalized text",
        },
        {
            "url": "http://example.test/child",
            "parent_url": "http://example.test/root",
            "crawl_depth": 1,
            "timestamp": "2026-09-22T20:00:01Z",
            "title": "Child",
            "normalized_text": "child normalized text",
            "entities": {key: [] for key in entities},
            "content": "child normalized text",
        },
    ]
    crawl_config = {"max_depth": 1, "max_pages": 20, "scope": "same_host"}

    with tempfile.TemporaryDirectory(prefix="robin-v1-persistence-") as temp_dir:
        root = Path(temp_dir)
        record = build_investigation_record(
            query="controlled query",
            refined_query="controlled refined query",
            model="test-model",
            preset_label="test-preset",
            sources=[{"link": "http://example.test/root", "title": "Root"}],
            crawl=crawl_config,
            pages=pages,
            summary="controlled summary",
            timestamp="2026-09-22T20:01:00",
        )

        assert record["crawl"] == crawl_config
        assert len(record["pages"]) == 2
        assert record["pages"][1]["parent_url"] == "http://example.test/root"
        assert record["pages"][1]["crawl_depth"] == 1
        assert record["pages"][0]["timestamp"] == "2026-09-22T20:00:00Z"
        assert record["pages"][0]["normalized_text"] == "root normalized text"
        assert record["pages"][0]["entities"]["cves"] == ["CVE-2024-12345"]
        assert "content" not in record["pages"][0]

        new_name = save_investigation(record, root)
        new_path = root / new_name
        assert new_path.exists()
        saved_json = json.loads(new_path.read_text(encoding="utf-8"))
        assert saved_json["pages"][1]["parent_url"] == "http://example.test/root"
        assert saved_json["crawl"] == crawl_config

        old_record = {
            "timestamp": "2026-01-01T10:00:00",
            "query": "legacy query",
            "refined_query": "legacy refined",
            "model": "legacy-model",
            "preset": "legacy-preset",
            "sources": [{"link": "http://legacy.example", "title": "Legacy"}],
            "summary": "legacy summary",
        }
        old_path = root / "investigation_20000101_000000.json"
        old_path.write_text(json.dumps(old_record, indent=2), encoding="utf-8")

        loaded = load_investigations(root)
        new_loaded = next(item for item in loaded if item.get("query") == "controlled query")
        old_loaded = next(item for item in loaded if item.get("query") == "legacy query")

        assert new_loaded["pages"][0]["entities"]["emails"] == ["analyst@example.com"]
        assert new_loaded["crawl"] == crawl_config
        assert "pages" not in old_loaded
        assert "crawl" not in old_loaded
        assert old_loaded["summary"] == "legacy summary"

    print("PASS: V1.3 saves crawl configuration and pages")
    print("PASS: persisted pages retain parent_url, crawl_depth and timestamp")
    print("PASS: persisted pages retain normalized_text and entities")
    print("PASS: new V1.3 investigation reloads correctly")
    print("PASS: legacy V0 investigation without pages/crawl reloads unchanged")
    print("PASS: persistence test requires no Tor, Internet or LLM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

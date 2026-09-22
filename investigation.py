"""Investigation persistence helpers for Robin V1.3.

The on-disk model remains one JSON file per investigation. Older Robin files
are loaded as-is and are never migrated or rewritten automatically.
"""

import json
from datetime import datetime
from pathlib import Path


INVESTIGATIONS_DIR = Path("investigations")


def _page_for_storage(page):
    """Return the stable V1.3 page schema without the V1.1 content alias."""
    return {
        "url": page.get("url", ""),
        "parent_url": page.get("parent_url"),
        "crawl_depth": page.get("crawl_depth", 0),
        "timestamp": page.get("timestamp", ""),
        "title": page.get("title", "Untitled"),
        "normalized_text": page.get("normalized_text", page.get("content", "")),
        "entities": page.get("entities", {}) or {},
    }


def build_investigation_record(
    query,
    refined_query,
    model,
    preset_label,
    sources,
    crawl,
    pages,
    summary,
    timestamp=None,
):
    """Build the JSON-serializable investigation record used by Robin V1.3."""
    return {
        "timestamp": timestamp or datetime.now().isoformat(),
        "query": query,
        "refined_query": refined_query,
        "model": model,
        "preset": preset_label,
        "crawl": dict(crawl or {}),
        "sources": list(sources or []),
        "pages": [_page_for_storage(page) for page in (pages or [])],
        "summary": summary,
    }


def save_investigation(record, investigations_dir=INVESTIGATIONS_DIR):
    """Save one investigation JSON file and return its filename."""
    investigations_dir = Path(investigations_dir)
    investigations_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"investigation_{timestamp}.json"
    (investigations_dir / fname).write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return fname


def load_investigations(investigations_dir=INVESTIGATIONS_DIR):
    """Load V0 or V1 investigations newest-first without migrating their schema."""
    investigations_dir = Path(investigations_dir)
    if not investigations_dir.exists():
        return []

    files = sorted(investigations_dir.glob("investigation_*.json"), reverse=True)
    investigations = []
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_filename"] = path.name
            investigations.append(data)
        except Exception:
            # Preserve Robin V0 behavior: one malformed file must not break the UI.
            continue
    return investigations

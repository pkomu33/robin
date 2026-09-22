#!/usr/bin/env python3
"""Local, offline smoke test for Robin V1.1 limited recursive crawler."""

import os
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Ensure local HTTP fixture never goes through an environment proxy.
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler import crawl  # noqa: E402


class RecordingHandler(SimpleHTTPRequestHandler):
    requests_seen = []

    def do_GET(self):
        type(self).requests_seen.append(self.path)
        super().do_GET()

    def log_message(self, format, *args):
        pass


def _write_fixture(root, port):
    root = Path(root)
    (root / "index.html").write_text(
        f"""<!doctype html>
<html><head><title>Root</title></head><body>
<a href="/child.html">child</a>
<a href="/child.html#duplicate">child duplicate</a>
<a href="http://localhost:{port}/outside.html">outside host</a>
<a href="mailto:test@example.com">mail</a>
</body></html>""",
        encoding="utf-8",
    )
    (root / "child.html").write_text(
        """<!doctype html>
<html><head><title>Child</title></head><body>
<a href="/grandchild.html#section">grandchild</a>
</body></html>""",
        encoding="utf-8",
    )
    (root / "grandchild.html").write_text(
        "<!doctype html><html><head><title>Grandchild</title></head><body>done</body></html>",
        encoding="utf-8",
    )
    (root / "outside.html").write_text(
        "<!doctype html><html><head><title>Outside</title></head><body>must not be crawled</body></html>",
        encoding="utf-8",
    )


def _by_path(pages):
    return {page["url"].split("?", 1)[0].rsplit("/", 1)[-1]: page for page in pages}


def main():
    with tempfile.TemporaryDirectory(prefix="robin-v1-smoke-") as fixture_dir:
        handler = partial(RecordingHandler, directory=fixture_dir)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        _write_fixture(fixture_dir, port)

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        root_url = f"http://127.0.0.1:{port}/index.html"

        try:
            RecordingHandler.requests_seen.clear()

            depth0 = crawl([root_url], max_depth=0, max_pages=10, same_host=True)
            assert len(depth0) == 1, depth0
            assert depth0[0]["url"] == root_url
            assert depth0[0]["parent_url"] is None
            assert depth0[0]["crawl_depth"] == 0

            RecordingHandler.requests_seen.clear()
            depth1 = crawl([root_url], max_depth=1, max_pages=10, same_host=True)
            assert len(depth1) == 2, depth1
            depth1_pages = _by_path(depth1)
            assert set(depth1_pages) == {"index.html", "child.html"}, depth1_pages
            assert depth1_pages["child.html"]["parent_url"] == root_url
            assert depth1_pages["child.html"]["crawl_depth"] == 1
            assert RecordingHandler.requests_seen.count("/child.html") == 1, RecordingHandler.requests_seen

            limited = crawl([root_url], max_depth=2, max_pages=2, same_host=True)
            assert len(limited) == 2, limited
            assert set(_by_path(limited)) == {"index.html", "child.html"}

            depth2 = crawl([root_url], max_depth=2, max_pages=10, same_host=True)
            depth2_pages = _by_path(depth2)
            assert set(depth2_pages) == {"index.html", "child.html", "grandchild.html"}, depth2_pages
            assert depth2_pages["grandchild.html"]["parent_url"].endswith("/child.html")
            assert depth2_pages["grandchild.html"]["crawl_depth"] == 2

            assert "/outside.html" not in RecordingHandler.requests_seen, RecordingHandler.requests_seen
            assert all("localhost" not in page["url"] for page in depth2)

            print("PASS: depth=0 fetches only root")
            print("PASS: depth=1 fetches root + child")
            print("PASS: max_pages is enforced")
            print("PASS: visited URLs prevent duplicate fetches")
            print("PASS: same-host scope blocks localhost link")
            print("PASS: parent_url is correct")
            print("PASS: crawl_depth is correct")
            print("PASS: smoke test used only local HTTP; Tor/Internet not required")
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())

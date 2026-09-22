#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "Missing .venv. Create it first with: python3 -m venv .venv" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import streamlit' >/dev/null 2>&1; then
    echo "Streamlit is not installed in .venv. Run: .venv/bin/python -m pip install -r requirements.lock.txt" >&2
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo "Warning: no .env file found. Copy .env.example to .env or provide configuration through environment variables." >&2
fi

exec "$PYTHON" -m streamlit run ui.py

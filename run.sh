#!/bin/sh
# One-command local start: creates the virtualenv, downloads the lists on first run, starts the server.
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  if command -v uv >/dev/null 2>&1 || [ -x "$HOME/.local/bin/uv" ]; then
    UV=$(command -v uv || echo "$HOME/.local/bin/uv")
    "$UV" venv --python 3.12 .venv && "$UV" pip install -q -r requirements-dev.txt --python .venv/bin/python
  else
    python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt
  fi
fi
[ -f data/sanctions.db ] || .venv/bin/python -m app.update
echo "Open http://localhost:${PORT:-8000}"
exec .venv/bin/uvicorn app.main:app --port "${PORT:-8000}"

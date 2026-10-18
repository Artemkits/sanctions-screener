#!/bin/sh
# Container entrypoint: make sure the lists are present (refresh if stale), then serve.
set -e
DATA_DIR="${DATA_DIR:-/app/data}"
DB="$DATA_DIR/sanctions.db"
HOURS="${REFRESH_HOURS:-24}"
if [ ! -f "$DB" ] || [ -n "$(find "$DB" -mmin +$((HOURS * 60)) 2>/dev/null)" ]; then
  echo "Downloading sanctions lists..."
  python -m app.update || echo "WARNING: update failed, serving existing data"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}"

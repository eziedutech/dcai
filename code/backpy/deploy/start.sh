#!/bin/sh
# Migrate, make sure the site lists exist, then serve.
set -e
alembic upgrade head
if [ ! -f "$SITE_LISTS_DIR/manifest.json" ]; then
  # First start only: build the lists from UT1 in the background; the phone retries later.
  python -u -m app.blocklist.build --out "$SITE_LISTS_DIR" > /tmp/blocklist.log 2>&1 &
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'

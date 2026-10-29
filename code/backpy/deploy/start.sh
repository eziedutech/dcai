#!/bin/sh
# Migrate, make sure the site lists exist, then serve.
set -e
# Fail fast on a stale migration lock instead of hanging the whole container (which leaves it
# "up but unhealthy" forever), and retry a few times before giving up so a redeploy recovers.
export PGOPTIONS="-c lock_timeout=10s -c statement_timeout=120s"
n=0
until alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 5 ]; then
    echo "alembic upgrade head failed after $n attempts" >&2
    exit 1
  fi
  echo "alembic upgrade head retry $n (db busy or locked); waiting..." >&2
  sleep 3
done
if [ ! -f "$SITE_LISTS_DIR/manifest.json" ]; then
  # First start only: build the lists from UT1 in the background; the phone retries later.
  python -u -m app.blocklist.build --out "$SITE_LISTS_DIR" > /tmp/blocklist.log 2>&1 &
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'

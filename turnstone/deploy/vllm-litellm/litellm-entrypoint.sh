#!/usr/bin/env bash
# LiteLLM entrypoint: wait for Postgres (spend tracking) before starting, fail-open.
set -euo pipefail

DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
  esac
done

DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-30}"

probe_tcp() {
  local host="$1" port="$2"
  timeout 2 bash -c "exec 3<>/dev/tcp/${host}/${port}" 2>/dev/null
}

wait_for_db() {
  local url="$1"
  # parse host/port from DATABASE_URL
  local host port
  host=$(python3 -c "import urllib.parse,sys; u=urllib.parse.urlparse(sys.argv[1]); print(u.hostname or 'localhost')" "$url")
  port=$(python3 -c "import urllib.parse,sys; u=urllib.parse.urlparse(sys.argv[1]); print(u.port or 5432)" "$url")
  echo "waiting for database at ${host}:${port} (timeout ${DB_WAIT_TIMEOUT}s)..." >&2
  local deadline=$((SECONDS + DB_WAIT_TIMEOUT))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if command -v pg_isready >/dev/null 2>&1; then
      if pg_isready -h "$host" -p "$port" >/dev/null 2>&1; then
        echo "database ready" >&2
        return 0
      fi
    else
      if probe_tcp "$host" "$port"; then
        echo "database ready (tcp)" >&2
        return 0
      fi
    fi
    sleep 1
  done
  echo "database not ready after ${DB_WAIT_TIMEOUT}s" >&2
  return 1
}

if [ -z "${DATABASE_URL:-}" ]; then
  echo "no DATABASE_URL — spend tracking disabled (fail-open)" >&2
else
  wait_for_db "$DATABASE_URL" || {
    echo "proceeding without db readiness (fail-open)" >&2
  }
fi

if [ "$DRY_RUN" = "true" ]; then
  exit 0
fi

exec litellm "$@"

#!/usr/bin/env bash
# Coffee Origin Monitor: local launcher (macOS / Linux).
#
#   ./dev.sh            demo mode: offline, synthetic data, opens the browser
#   ./dev.sh live       real data from every free source, local SQLite archive
#   ./dev.sh test       run the test suite
#   ./dev.sh reset      delete the local demo + live archives (data/)
#   ./dev.sh docker     build and run the production container locally
#
# The first run creates a .venv and installs dependencies (about a minute).
# Edits to app/ reload the server automatically; refresh the browser.
set -euo pipefail
cd "$(dirname "$0")"

CMD="${1:-demo}"
PORT="${PORT:-8080}"

find_python() {
  for p in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      echo "$p"; return
    fi
  done
  echo "Python 3.10 or newer is required." >&2
  echo "  macOS:  brew install python@3.12   (or download from python.org)" >&2
  exit 1
}

setup() {
  if [[ ! -x .venv/bin/python ]]; then
    PY=$(find_python)
    echo "▸ Creating virtual environment with $($PY --version)"
    "$PY" -m venv .venv
  fi
  if [[ ! -f .venv/.deps-ok ]] || [[ requirements-local.txt -nt .venv/.deps-ok ]]; then
    echo "▸ Installing dependencies"
    .venv/bin/python -m pip install -q --upgrade pip
    .venv/bin/python -m pip install -q -r requirements-local.txt
    touch .venv/.deps-ok
  fi
  [[ -f .env ]] || { cp .env.example .env; echo "▸ Created .env from .env.example (edit it to add optional API keys)"; }
}

open_browser() {
  local url="http://localhost:${PORT}/#/$1"
  ( sleep 2
    if command -v open >/dev/null; then open "$url"
    elif command -v xdg-open >/dev/null; then xdg-open "$url" >/dev/null 2>&1
    fi ) &
}

serve() {
  local mode="$1"
  setup
  echo
  echo "  Coffee Origin Monitor · ${mode} mode"
  echo "  http://localhost:${PORT}"
  [[ "$mode" == demo ]] && echo "  Offline demo data. Run ./dev.sh live for real sources."
  [[ "$mode" == live ]] && echo "  First news run takes ~1 min; watch progress on the Sources and Dev pages."
  echo "  Ctrl+C to stop."
  echo
  [[ "${NO_BROWSER:-}" == 1 ]] || open_browser ""
  APP_MODE="$mode" exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" \
    --reload --reload-dir app --log-level warning
}

case "$CMD" in
  demo|live) serve "$CMD" ;;
  test)
    setup
    APP_MODE=demo GDELT_DELAY=0 .venv/bin/python -m pytest -q tests ;;
  reset)
    rm -rf data && echo "▸ Deleted data/ (demo reseeds on next start)" ;;
  docker)
    command -v docker >/dev/null || { echo "Docker isn't installed."; exit 1; }
    docker build -t coffee-monitor .
    echo "▸ http://localhost:${PORT} (demo mode inside the production container)"
    docker run --rm -p "${PORT}:8080" -e APP_MODE=demo coffee-monitor ;;
  *)
    sed -n '2,12p' "$0"; exit 1 ;;
esac

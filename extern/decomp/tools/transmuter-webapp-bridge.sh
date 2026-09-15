#!/bin/bash
# Poll Transmuter HTTP API /report and feed the session webapp JSON path.
# Writes a complete file to *.partial then atomically `mv`s it into place so
# the report is never half-written. The dev-server re-attaches fs.watch on
# Linux 'rename' when the inode is replaced.
#
# Usage:
#   tools/transmuter-webapp-bridge.sh [control.json path]
# Default control path:
#   build/G4QE01/src/Game/Sys/transmuter-control.json  (first match under build/)
#
# Prerequisites: transmuter match … --api (writes transmuter-control.json)

set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

CONTROL="${1:-}"
if [ -z "$CONTROL" ]; then
  CONTROL="$(find build -name transmuter-control.json -type f -mmin -120 2>/dev/null | head -1 || true)"
fi
if [ -z "$CONTROL" ] || [ ! -f "$CONTROL" ]; then
  echo "error: transmuter-control.json not found. Start a match with --api or pass its path." >&2
  exit 1
fi

PORT="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))[\"port\"])" "$CONTROL")"
OUT="${TRANSMUTER_WEBAPP_JSON:-/tmp/transmuter-live/session-live.json}"
mkdir -p "$(dirname "$OUT")"
TMP="${OUT}.partial.$$"

echo "polling http://127.0.0.1:${PORT}/report -> $OUT (every 2s)"

  while true; do
  if curl -sS --fail -m 8 "http://127.0.0.1:${PORT}/report" -o "$TMP" 2>/dev/null; then
    if [ -s "$TMP" ]; then
      # Atomic rename so readers never see a half-written file. dev-server
      # re-attaches fs.watch on 'rename' after this.
      mv -f "$TMP" "$OUT"
    fi
  else
    echo "[$(date +%H:%M:%S)] report fetch failed (is the match still running?)" >&2
  fi
  rm -f "$TMP"
  sleep 2
done

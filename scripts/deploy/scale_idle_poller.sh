#!/usr/bin/env bash
# Idle scale poller -- runs ON the Pi, streams the balance into MongoDB.
#
# Deliberately not installed by anything in this repo: it holds
# /dev/ttyACM0 for as long as it runs, so it has to yield the port to
# dose/characterization runs.  Install it only once that hand-off is
# decided (see docs/scale-idle-streaming-results.md, "next steps").
#
#   sudo cp scripts/deploy/scale-idle-poller.service /etc/systemd/system/
#   sudo install -m 600 /dev/null /etc/powder-doser.env   # then add MONGODB_URI=
#   sudo systemctl daemon-reload && sudo systemctl enable --now scale-idle-poller
set -euo pipefail

REPO="${REPO:-$HOME/powder-doser}"
VENV="${VENV:-$HOME/powder-doser-venv}"
PORT="${PORT:-/dev/ttyACM0}"
POLL_HZ="${POLL_HZ:-5}"
CHUNK_S="${CHUNK_S:-3600}"          # restart the device script hourly
SPOOL="${SPOOL:-$HOME/.local/state/powder-doser/scale-spool.jsonl}"

mkdir -p "$(dirname "$SPOOL")"
RUN=$(mktemp /tmp/scale_stream_run.XXXXXX.py)
trap 'rm -f "$RUN"' EXIT

# The device script takes its duration/rate as prepended globals; a
# bounded chunk means a wedged UART self-heals within the hour instead
# of silently streaming nothing until someone notices.
{
  printf 'DURATION_S = %s\nPOLL_HZ = %s\n' "$CHUNK_S" "$POLL_HZ"
  cat "$REPO/hardware/test-module/firmware/scale_stream.py"
} > "$RUN"

exec "$VENV/bin/mpremote" connect "$PORT" run "$RUN" \
  | "$VENV/bin/python" "$REPO/scripts/scale_stream_capture.py" - \
      --upload --flush-every 30 --spool "$SPOOL" --quiet

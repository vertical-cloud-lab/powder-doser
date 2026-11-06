#!/usr/bin/env bash
# Run a read-only FTPS script against a Bambu printer, relayed through the doser Pi.
#
#   run_on_pi.sh <H2D|A1_MINI> <script.py> [more .py files, concatenated in order]
#
# The printer's IP and LAN access code (<PRINTER>_IP, <PRINTER>_ACCESS_CODE) and the
# scripts go over the SSH session's stdin, so no secret is put on a command line or on
# disk on either machine. The remote Python gets them as `ip` and `code`.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
p="$1"; shift
ipvar="${p}_IP"; codevar="${p}_ACCESS_CODE"
{
  printf '%s\n' "${!ipvar}"
  printf '%s\n' "${!codevar}"
  cat "$here/ftps_common.py" "$@"
} | ssh -o BatchMode=yes -o ConnectTimeout=20 "$RPI_POWDER_DOSER_USERNAME@$RPI_POWDER_DOSER_HOSTNAME" \
  'python3 -u -c "import sys; ip=sys.stdin.readline().strip(); code=sys.stdin.readline().strip(); exec(compile(sys.stdin.read(), \"remote\", \"exec\"))"'

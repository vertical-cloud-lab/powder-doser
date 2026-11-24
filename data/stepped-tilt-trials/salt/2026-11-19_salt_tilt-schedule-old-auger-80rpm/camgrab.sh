#!/bin/bash
# Pi side: fetch the newest HLS segment of the bench livestream (rate-capped). Usage: camgrab.sh <video_id> <outdir>
set -e
VID=$1; OUT=$2; mkdir -p "$OUT"; cd "$OUT"
Y=~/powder-doser-venv/bin/yt-dlp
if [ ! -s .m3u8_url ] || [ $(( $(date +%s) - $(stat -c %Y .m3u8_url) )) -gt 3000 ]; then
  $Y -q --no-warnings -g -f 232 "https://www.youtube.com/watch?v=$VID" > .m3u8_url
fi
curl -s --limit-rate 300k "$(cat .m3u8_url)" > media.m3u8
SEG=$(grep -v '^#' media.m3u8 | tail -1)
curl -s --limit-rate 300k "$SEG" -o seg.ts
grep -m1 "EXT-X-PROGRAM-DATE-TIME" media.m3u8 | cut -c1-80 || true
ls -la seg.ts | awk '{print $5}'

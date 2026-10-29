#!/bin/bash
# Ensure a SOCKS5 tunnel through the doser Pi on 127.0.0.1:1080 (residential IP). Prints only status.
if ss -ltn 2>/dev/null | grep -q '127.0.0.1:1080 '; then echo "tunnel: up"; exit 0; fi
ssh -f -N -D 127.0.0.1:1080 -o LogLevel=ERROR -o StrictHostKeyChecking=no -o BatchMode=yes \
    -o ServerAliveInterval=20 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes \
    "$RPI_POWDER_DOSER_USERNAME@$RPI_POWDER_DOSER_HOSTNAME" && sleep 1
ss -ltn 2>/dev/null | grep -q '127.0.0.1:1080 ' && echo "tunnel: started" || echo "tunnel: FAILED"

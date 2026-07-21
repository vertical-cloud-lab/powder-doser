#!/usr/bin/env python3
"""Step 2 - H2D reachability smoke test (no print). Win/macOS/Linux.

Verifies the (IP, ACCESS_CODE, SERIAL) triple against the printer:
  2b. MQTT-over-TLS on :8883 - subscribes to device/<SERIAL>/report and
      waits up to 15 s for one telemetry message.
  2c. Implicit FTPS on :990 with TLS 1.2 session reuse - lists /cache.

This is the exact script verified against the real H2D (serial
0947AJ622500469) in PR #23 on 2026-05-21, including the two client-side
fixes that took two rounds to find: implicit-FTPS socket wrapping (stdlib
FTP_TLS is explicit and times out) and RFC 5077 data-channel session
reuse pinned to TLS 1.2 (else `522 SSL connection failed: session reuse
required`). See docs/h2d-programmatic-access.md, Step 2, for the full
troubleshooting walkthrough.

    pip install paho-mqtt
    python h2d_smoketest.py --ip <IP> --access-code <CODE> --serial <SERIAL>

Credentials may also be supplied via the H2D_IP / H2D_ACCESS_CODE /
H2D_SERIAL environment variables.
"""

import argparse
import ftplib
import os
import socket
import ssl
import sys
import threading

import paho.mqtt.client as mqtt


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS for the H2D's *implicit* FTPS on :990.

    The H2D starts the TLS handshake immediately on TCP connect (no
    plaintext `220` banner, no `AUTH TLS`), so the socket must be wrapped
    before the first read. The data channel additionally must resume the
    control channel's TLS session (RFC 5077) or the printer answers
    `522 SSL connection failed: session reuse required`.
    """

    def connect(self, host="", port=0, timeout=-999, source_address=None):
        if host:
            self.host = host
        if port:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        if source_address is not None:
            self.source_address = source_address
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.af = self.sock.family
        self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
        self.file = self.sock.makefile("r", encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size


def make_ftps_context():
    # Session resumption only works when control and data sockets share one
    # SSLContext advertising TLS 1.2 (the H2D's FTPS server has no TLS 1.3
    # session tickets). The printer's cert is self-signed by design.
    ctx = ssl._create_unverified_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def add_credential_args(parser):
    parser.add_argument("--ip", default=os.environ.get("H2D_IP"),
                        help="printer IP (or set H2D_IP)")
    parser.add_argument("--access-code", default=os.environ.get("H2D_ACCESS_CODE"),
                        help="8-digit LAN access code (or set H2D_ACCESS_CODE)")
    parser.add_argument("--serial", default=os.environ.get("H2D_SERIAL"),
                        help="15-char printer serial (or set H2D_SERIAL)")


def require_credentials(args, parser):
    missing = [n for n, v in
               [("--ip", args.ip), ("--access-code", args.access_code),
                ("--serial", args.serial)] if not v]
    if missing:
        parser.error("missing " + ", ".join(missing) +
                     " (flags or H2D_IP/H2D_ACCESS_CODE/H2D_SERIAL env vars)")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_credential_args(parser)
    args = parser.parse_args()
    require_credentials(args, parser)
    ip, code, serial = args.ip, args.access_code, args.serial
    ok = True

    # 2b. MQTT-over-TLS - wait up to 15 s for the first report, then move on
    print("Connecting MQTT...")
    got = threading.Event()

    def on_msg(c, u, m):
        print("MQTT OK:", m.topic, m.payload[:120], "...")
        got.set()

    c = mqtt.Client()
    c.username_pw_set("bblp", code)
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.on_message = on_msg
    try:
        c.connect(ip, 8883, 30)
        c.subscribe(f"device/{serial}/report")
        c.loop_start()
        if not got.wait(timeout=15):
            ok = False
            print("MQTT WARN: connected but no report in 15 s "
                  "(check SERIAL - FTPS check will still run below)")
        c.loop_stop()
        c.disconnect()
    except Exception as e:
        ok = False
        print(f"MQTT ERROR: {e}")

    # 2c. Implicit FTPS with TLS 1.2 session reuse - list /cache
    print("Connecting FTPS...")
    try:
        ftps = ImplicitFTP_TLS(context=make_ftps_context())
        ftps.connect(ip, 990, 30)
        ftps.login("bblp", code)
        ftps.prot_p()
        print("FTPS /cache:", ftps.nlst("/cache"))
        ftps.quit()
    except Exception as e:
        ok = False
        print(f"FTPS ERROR: {e}")

    print("Smoke test complete.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

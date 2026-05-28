"""Tiny non-blocking single-keypress reader shared by the test scripts.

CircuitPython exposes :mod:`supervisor` so we can poll
``serial_bytes_available`` and then ``sys.stdin.read(n)`` without
blocking the main loop -- this is what lets us treat each USB-serial
keystroke from the bench operator as an "event" (e.g. spacebar fires
the haptic motor) instead of having to type a command + Enter.

Falls back to a blocking ``sys.stdin.read(1)`` on CPython (handy when
unit-checking the helper outside the Pico).
"""

from __future__ import annotations

import sys


def read_key() -> str | None:
    """Return one buffered character if available, else ``None``.

    Newlines (``\\r`` and ``\\n``) are normalised to ``"\\n"`` so the
    test scripts can match on a single character regardless of the
    terminal's line-ending convention.
    """
    try:
        import supervisor
        n = supervisor.runtime.serial_bytes_available
    except (ImportError, AttributeError):
        # CPython / desktop -- fall back to blocking single-char read.
        ch = sys.stdin.read(1)
        return ch or None
    if not n:
        return None
    ch = sys.stdin.read(1)
    if ch in ("\r", "\n"):
        return "\n"
    return ch

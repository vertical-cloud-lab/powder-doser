"""Non-blocking single-keystroke reader for MicroPython on the Pico W.

MicroPython doesn't expose CircuitPython's ``supervisor.runtime`` so we
use ``uselect.poll()`` on ``sys.stdin`` instead.  Each test script
calls :func:`read_key` once per main-loop iteration and treats every
returned character as an event (e.g. spacebar fires the haptic motor),
so the operator can drive the bench rig from the MicroPico VS Code
terminal without having to type a command + Enter.

CPython has neither ``uselect`` nor a non-blocking stdin by default,
so on the desktop the helper falls back to a blocking ``sys.stdin.read(1)``
which is enough for unit-checking the helper offline.
"""

import sys

try:
    import uselect  # MicroPython
    _poll = uselect.poll()
    _poll.register(sys.stdin, uselect.POLLIN)
    _HAVE_POLL = True
except ImportError:
    _HAVE_POLL = False


def read_key():
    """Return one buffered character if available, else ``None``.

    ``\\r`` and ``\\n`` are both normalised to ``"\\n"`` so the test
    scripts can match on a single character regardless of the
    terminal's line-ending convention.
    """
    if _HAVE_POLL:
        if not _poll.poll(0):
            return None
        ch = sys.stdin.read(1)
    else:
        ch = sys.stdin.read(1)
        if not ch:
            return None
    if ch in ("\r", "\n"):
        return "\n"
    return ch

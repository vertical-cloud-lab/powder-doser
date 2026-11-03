"""Tare-and-stream raw balance logger for manual bench tests.

Minimal data-collection helper for operator-run experiments such as the
balance step-response (tau_bal) drop-weight test: it tares the scale
once at the start, then streams every raw frame -- INCLUDING
unstable-flagged ones, which are the data -- for a chosen duration, and
ends with one settled stable reading (the ground truth for a step's
final value).  No actuators are touched; the auger, taps, and servo
stay wherever they are.

The capture is SAVED TO A FILE ON THE PICO named by ``OUTPUT_FILE``
below -- edit that name per test (e.g. "a1_drop_0p5g_rep01.csv"), run,
rename for the next rep, run again.  Every row is still echoed to the
console so you can watch the mass and S-flags live.  The operator
records externally what mass was used; nothing about the experiment
design lives in here.

How to run
----------
Under MicroPico ("Run current file"): set ``OUTPUT_FILE`` (and
optionally ``DURATION_S``) below, run, and answer the duration prompt
if you left ``DURATION_S = None``.  Press Enter (optionally after
typing a note) at any moment during the stream to drop an
``E,<t_ms>,mark...`` row -- e.g. the instant you release the weight.

Under bare ``mpremote run balance_stream.py``: set ``DURATION_S`` to a
number first -- mpremote does not forward keyboard input, so the
prompt would hang forever.

Copying the files off the Pico afterwards:

    mpremote fs ls
    mpremote fs cp :a1_drop_0p5g_rep01.csv a1_drop_0p5g_rep01.csv

(or use MicroPico's "Download project" / file view).  An existing file
is never overwritten unless you set ``OVERWRITE = True``, so a
forgotten rename aborts loudly instead of clobbering the previous rep.

The host wrapper (``python balance_stream_host.py 40 out.csv``) still
works as before; it saves on the PC and disables the on-Pico file.

Requires PR #100's ``config.py`` / ``scale.py`` / ``tic.py`` plus this
branch's ``main_three_phase.py`` on the Pico (same set the resident
firmware already needs).

Output rows (CSV, identical in the file and on the console)
-----------------------------------------------------------
    M,<key>,<value>           metadata (duration, poll cadence, label)
    P,<t_ms>,<kind>,<grams>   settled stable reading; kind: pretare,
                              tare0, settled
    E,<t_ms>,<text>           event (tare done, progress ticks, marks)
    D,<t_ms>,<grams>,<flag>   raw frame; flag S=stable, U=unstable,
                              X=no/garbled response (grams then "nan")
"""

import os
import sys
import time

# ---------------------------------------------------------------------------
# Settings.  Name each capture here before running; set OUTPUT_FILE = None
# for console-only streaming (the host runner does this automatically and
# saves on the PC instead).  Leave DURATION_S = None to be prompted when
# run interactively.
# ---------------------------------------------------------------------------
OUTPUT_FILE = "balance_capture.csv"  # saved on the Pico; rename per test
OVERWRITE = False       # True lets a run replace an existing OUTPUT_FILE
DURATION_S = None       # stream length in seconds; None -> prompt on stdin
LABEL = ""              # optional free-text tag echoed into the metadata
POLL_MS = 60            # scale poll cadence (the HR-100A answers ~10.4 Hz)
STABLE_TIMEOUT_MS = 8000
PROGRESS_EVERY_S = 10   # progress E-row cadence during the stream

import main_three_phase as m3

_t0 = time.ticks_ms()
_file = None


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def out(line):
    """One CSV row: echo to the console and append to the capture file."""
    print(line)
    if _file is not None:
        _file.write(line + "\n")
        _file.flush()


def ev(msg):
    out("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    out("M,{},{}".format(k, v))


def _open_output():
    global _file
    if not OUTPUT_FILE:
        return
    if not OVERWRITE:
        try:
            os.stat(OUTPUT_FILE)
        except OSError:
            pass  # does not exist yet -- good
        else:
            print("REFUSING to overwrite existing {!r}; rename OUTPUT_FILE "
                  "for this test or set OVERWRITE = True".format(OUTPUT_FILE))
            sys.exit(1)
    _file = open(OUTPUT_FILE, "w")


def _close_output(n):
    global _file
    if _file is None:
        return
    _file.close()
    _file = None
    try:
        os.sync()
    except (AttributeError, OSError):
        pass
    print("saved {} samples to {!r} on the Pico -- copy off with:".format(
        n, OUTPUT_FILE))
    print("    mpremote fs cp :{0} {0}".format(OUTPUT_FILE))


# -- optional Enter-to-mark during the stream (MicroPico only; harmless
#    no-op under mpremote, where stdin never delivers anything) -------------
try:
    import uselect
    _poll = uselect.poll()
    _poll.register(sys.stdin, uselect.POLLIN)
except ImportError:
    _poll = None
_mark_buf = ""


def _check_mark():
    global _mark_buf
    if _poll is None:
        return None
    while _poll.poll(0):
        ch = sys.stdin.read(1)
        if ch in ("\r", "\n"):
            line, _mark_buf = _mark_buf, ""
            return "mark " + line if line else "mark"
        _mark_buf += ch
    return None


def _ask_duration():
    while True:
        try:
            raw = input("stream duration seconds: ").strip()
            secs = float(raw)
            if secs > 0:
                return secs
        except ValueError:
            pass
        print("enter a positive number of seconds")


def settled(scale, kind):
    r = scale.read_stable(timeout_ms=STABLE_TIMEOUT_MS)
    if r is None or r.grams is None:
        ev("no stable frame for {}; logging last raw read".format(kind))
        r = scale.read()
    g = None if (r is None or r.grams is None) else r.grams
    out("P,{},{},{}".format(
        t_ms(), kind, "nan" if g is None else "{:.4f}".format(g)))
    return g


def main():
    dur = DURATION_S if DURATION_S is not None else _ask_duration()
    _open_output()
    n = 0
    try:
        scale = m3.Scale()
        meta("script", "balance_stream")
        meta("duration_s", "{:.1f}".format(dur))
        meta("poll_ms", POLL_MS)
        if LABEL:
            meta("label", LABEL)
        if OUTPUT_FILE:
            meta("output_file", OUTPUT_FILE)

        # Absolute (pre-tare) settled reading for cup bookkeeping, then tare.
        settled(scale, "pretare")
        scale.zero()
        ev("tared")
        settled(scale, "tare0")

        ev("streaming for {:.1f} s -- raw frames follow".format(dur))
        end = time.ticks_add(time.ticks_ms(), int(dur * 1000))
        next_progress = time.ticks_add(time.ticks_ms(),
                                       int(PROGRESS_EVERY_S * 1000))
        try:
            while time.ticks_diff(end, time.ticks_ms()) > 0:
                r = scale.read()
                ts = t_ms()
                if r is None or r.grams is None:
                    out("D,{},nan,X".format(ts))
                else:
                    out("D,{},{:.4f},{}".format(
                        ts, r.grams, "S" if r.stable else "U"))
                n += 1
                mark = _check_mark()
                if mark is not None:
                    ev(mark)
                if time.ticks_diff(next_progress, time.ticks_ms()) <= 0:
                    remaining = time.ticks_diff(end, time.ticks_ms()) / 1000.0
                    ev("progress: {:.0f} s remaining".format(remaining))
                    next_progress = time.ticks_add(
                        time.ticks_ms(), int(PROGRESS_EVERY_S * 1000))
                time.sleep_ms(POLL_MS)
        except KeyboardInterrupt:
            ev("interrupted by operator after {} samples".format(n))

        settled(scale, "settled")
        ev("done ({} samples)".format(n))
    finally:
        _close_output(n)


if __name__ == "__main__":
    main()

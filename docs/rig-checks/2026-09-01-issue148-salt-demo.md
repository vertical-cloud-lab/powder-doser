# 2026-09-01 — issue #148 live-demo salt run (2 g target)

Short single-dose run requested for a live demo: block G only, one
closed-loop dose, `dose_target_g=2.0`, powder `salt`, unattended.

    ~/powder-doser-venv/bin/python scripts/powder_battery_capture.py \
      --port /dev/ttyACM0 --powder-id salt --operator claude --unattended \
      --run-args 'blocks="G", dose_repeats=1, dose_target_g=2.0'

## Outcome — no powder was dispensed

Two attempts, neither delivered salt. The controller behaved correctly
in both; the fault is upstream of the software.

### Attempt 1 — `20260901T164137Z_salt/` — `scale-error`

The A&D HR-100A was switched off, so the tare at the head of the dose
never returned a frame:

    [dose] three-phase dose to 2.0000 g; taring scale
    DOSE,0,2.0000,0.0000,-2.0000,scale-error,13.0,0.00,0,,13293

The doser refused to turn the auger at all (`0.00 auger rev`) — with no
balance there is no closed loop, so this is the intended failure mode
rather than an open-loop guess.

Probing the balance UART straight from the Pico confirmed it: a `Q`
query drew zero bytes in 3 s (`RAW after Q: b''`) at 19200 8N1 on
tx=GP12 / rx=GP13. After the operator powered the balance on, the same
probe returned `US,+000.0003  g` and then steady `ST` frames.

### Attempt 2 — `20260901T164658Z_salt/` — `stalled`, no feed

With the balance live the loop ran properly and the auger did turn, but
the balance never gained mass:

    === phase 1/3 'bulk' start: 2.0000 g to go [...] CONTINUOUS @ 55 auger rpm
    [phase 1 bulk] poll 16 (unstable): mass -0.0389 / 2.0000 g
    [phase 1 bulk] no powder flow for 4.0 s while spinning -- hopper empty or jam
    DOSE,0,2.0000,-0.0389,-2.0389,stalled,8.0,4.58,0,bulk:16,8142

4.58 auger revolutions at 45 deg plate produced no gain. For scale, the
2026-08-21 salt run (`20260821T192031Z_salt/`) measured **0.6296 g mean
over 3 revolutions** in block D at the same tilt, so roughly a gram was
expected here.

The small negative drift is balance warm-up, not powder leaving the pan:
a 24 s watch immediately afterwards sat at approximately -0.023 g with
mostly `ST` frames, two orders of magnitude short of the missing 2 g.

### Feed diagnostic — `feed_diagnostic_stage1.log`

`battery_feed_diagnostic` was started to separate arching from
mechanical no-feed. Stage 1 — ten continuous revolutions at 60 RPM at
tilt 90 deg, the most favourable geometry the rig has — conveyed
nothing:

    DIAG,long,10rev@60rpm,-0.0159,-0.0280,-0.0121,3600.0,

The remaining stages (`fast`, `agitate`) did not run: a second agent
session opened `/dev/ttyACM0` for `balance_zero.py` and took the port
mid-run. Stage 1 alone does not discriminate between the diagnostic's
"mechanical no-feed" and "empty column" verdicts, both of which are
consistent with dead rotation at 90 deg; it does rule out simple
slow-but-workable cohesion, which stage 1 is designed to reveal.

Remaining candidates, in the diagnostic's own terms: empty hopper,
auger not seated in the coupler, a capped or blocked outlet, or a
collection cup that is not under the outlet. All four need eyes at the
bench.

## MongoDB

The attempt-2 run document is in `powder_doser.battery_runs` as
`_id 6a97025021119262684581ca`. It is uploaded verbatim as the capture
wrote it — a `stalled` dose with `dispensed_g = -0.0389` is a real
observation of the rig's no-feed state, not a discarded run.

Attempt 1 (`20260901T164137Z_salt/`) was not uploaded: with a dead
balance it carries no measurement, only the `scale-error` status.

## Rig note

`/dev/ttyACM0` was held on arrival by an orphaned `mpremote repl`
(PID 1483, started 2026-08-27, parent shell reparented to init, no
operator logged in on its tty). It was killed to free the port. Worth
checking that whatever leaves those REPLs behind exits cleanly, since a
held port blocks every capture.

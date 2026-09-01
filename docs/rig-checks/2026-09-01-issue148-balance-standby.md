# 2026-09-01 — issue #148: why the balance was "off", and how to tell

The issue #148 demo opened with the A&D HR-100A dark. The doser reported
`scale-error` and refused to turn the auger, which was the right call, but
nobody could say *why* the balance was off — it had not been touched, and a
balance in standby looks exactly like a balance that is unplugged.

This note records what was measured on the rig that evening: the serial
signature of standby, a timed test of the balance's own auto-off feature,
and the state left on the bench.

## Summary

The HR-A series has no power switch in the usual sense. `ON:OFF` toggles
**standby**, and the balance also enters standby whenever AC power is
interrupted and restored. Standby is a normal state (manual §3-4) and its
only indication is a small standby marker on an otherwise blank LCD.

Two mechanisms can produce a dark balance with no operator action:

| mechanism | function-table item | measured on this unit |
|---|---|---|
| timed auto display-OFF after ~10 min idle at ≤ 0.5 g | `poff` "Auto display-OFF" | **did not fire** — see below |
| AC interrupted → returns to standby, not weighing | `p-on` "Auto display-ON" | not directly testable remotely |

So a *timed* auto-off is not what happened here, as the balance is
configured today. A power interruption (or a single `ON:OFF` press) is the
remaining explanation, and neither leaves a trace.

## The serial signature of standby

Measured through the Pico's balance UART (19200 8N1), replicated twice, by
sending the documented `OFF` command and probing:

| command | awake | standby |
|---|---|---|
| `?TN` (model) | `TN,   HR-100A` | `TN,   HR-100A` — **still answers** |
| `?ID` | `ID,0000000` | `ID,0000000` — still answers |
| `Q` (weight now) | `ST,+068.7857  g` | *(silence)* |
| `S` (weight when stable) | datum | *(silence)* |

`Q` and `S` go silent because the balance is not in weighing mode; that is
error `E11` "Not ready" (manual §19-2), and with error-code output disabled
the balance simply says nothing. This is exactly what the failed 16:37 UTC
attempt saw: `RAW after Q: b''`.

Neither `Q` nor `S` wakes the balance. `ON` does.

**This is the useful part: `?TN` distinguishes the two failure modes.**

- `?TN` answers, `Q` silent → balance is in **standby**; send `ON`.
- `?TN` silent as well → genuinely absent: no power, cable, or a baud
  mismatch.

The current firmware only ever sends `Q`/`S`, so both cases surface as
"no samples" / `scale-error`.

### Waking it costs a zero, and takes longer than you expect

`ON` re-enters weighing mode and **resets the zero/tare reference**:

- `ON` sent while already awake cleared the tare — the display went from
  `+001.8916 g` (net, cup tared) to `+068.7857 g` (gross).
- `OFF` then `ON` re-zeroed at the current load — `+068.8 g` became
  `-000.0032 g`.

And the transition is slow. Weighing data came back in under 5 s on one
attempt but took more than 12 s on another, so anything that auto-wakes the
balance should allow **~15 s** before treating silence as a failure, then
tare before dosing. Note also that the manual asks for a one-hour warm-up
after auto display-ON for accurate weighing.

## Timed test of `poff`

`poff` turns the display off "if the weighing value is 0.5 g or less and the
balance is in the no key operation or no command has been received for
approx. 10 minutes" (manual §10-3, "Auto display-OFF (`poff`)").

Both preconditions were set up deliberately and the balance was left alone:

| | |
|---|---|
| displayed value at `t0` | `US,-000.0276  g` (≤ 0.5 g ✓) |
| `t0` | 2026-09-01 21:37:55 UTC |
| `t1` | 2026-09-01 21:51:03 UTC (13.0 min, zero UART traffic) |
| reading at `t1` | `US,-000.0354  g` — **still weighing** |

13 minutes is 30 % past the documented 10-minute timer, so `poff` is
almost certainly set to `0` (OFF) on this unit. Two caveats, stated
because the test is behavioural rather than a read of the function table
(the A&D command set has no function-table read command):

1. Every frame during the window was `US` (unstable). The manual does not
   say the value must be *stable* for the timer to run, but it does not say
   it must not be, either.
2. A separate observation points the same way: the balance sat idle for
   4 h 41 min after the 16:50 UTC run and was still awake — though with
   1.89 g on the pan, above the 0.5 g threshold, so that one is only
   consistent, not decisive.

## What to change

**On the balance** (function table; hold `SAMPLE` from weighing mode to
enter at `ba5fnc`, `SAMPLE` steps items, `RE-ZERO` changes the parameter,
`PRINT` stores — manual §10-1/10-2):

- Set **`p-on` = 1** ("Auto display-ON"). The manual's own note on this item
  is *"Used when the balance is built into an automated system."* With it
  set, any power blip self-heals into weighing mode instead of parking in
  standby. Parameters live in non-volatile memory and survive the adapter
  being removed.
- Confirm **`poff` = 0** while in there, so the timed path is ruled out by
  inspection rather than by the test above.

**In the firmware/capture stack** (not implemented here — recorded as the
obvious follow-up):

- Probe `?TN` before declaring `scale-error`, and report "balance in
  standby" separately from "balance not responding".
- Optionally recover automatically: `ON`, wait ~15 s, tare, retry.
- Record the balance's wake state in the run document, so a run that had to
  wake the balance is visible later without reading logs.

**On the Pi:** `journald` is volatile here (`journalctl --list-boots` shows
only the current boot) and `wtmp` is empty, so the reboot at
2026-08-27 ~13:32 UTC — the same day someone left the orphaned `mpremote`
noted in issue #148 — cannot be attributed to a power event or to a manual
reboot. Setting `Storage=persistent` in `journald.conf` would make the next
occurrence answerable.

## Timeline of the outage

| when | what |
|---|---|
| 2026-08-21 19:20 UTC | last successful battery run; balance working |
| 2026-08-27 ~13:32 UTC | Pi reboots (cause unrecoverable — volatile journal) |
| 2026-08-27 ~19:37 UTC | `mpremote repl` started and left running |
| 2026-09-01 16:37 UTC | demo starts, balance dark, `Q` returns nothing |
| 2026-09-01 16:46 UTC | balance powered on by hand; `US,+000.0003 g` |

## Pi-side state changed by this investigation

Per `CLAUDE.md`, changes made on the Pi are recorded here.

- **The balance's zero reference was reset.** Probing sent `ON`/`OFF`/`ON`,
  which re-zeroes at whatever is on the pan. The balance was left **awake
  and weighing at ≈ 0.000 g with the collection cup and ~1.9 g of salt
  still on it** — so emptying the cup will make the display read about
  −1.9 g until it is re-zeroed. `scripts/balance_zero.py` (or the tare at
  the start of any capture) restores a sane zero.
- No motion was commanded: no stepper, servo or solenoid, and no dose.
- Temporary probe scripts were written to `/tmp` on the Pi and deleted.

## Reference

A&D HR-AZ/HR-A series instruction manual (HR-100A):
§3-4 Power Supply · §4 Display Symbols and Key Operation ·
§10-1/10-2/10-3 Function Table (`p-on`, `poff`) ·
§17-1 Command List (`ON`, `OFF`, `P`, `Q`, `S`, `?TN`, `?ID`) ·
§19-2 error codes (`E11` "Not ready").
<https://weighing.andonline.com/wp-content/uploads/2024/01/HR-A_HR-AZ_Manual_02.pdf>

# Bench debugging with a local agent (Claude Code + mpremote)

The PR #100 RS-232 bring-up showed the limits of debugging through a
GitHub comment thread: each hypothesis costs a day of round-trip.  This
guide sets up the loop @sgbaird proposed instead — **Claude Code
running on the bench laptop, driving the Pico directly** over USB, with
the human only touching wires when asked.

## 1. One-time setup on the bench laptop

1. Install [VS Code](https://code.visualstudio.com/) and the
   [Claude Code extension](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)
   (or the [CLI](https://docs.anthropic.com/en/docs/claude-code)).
2. Clone this repo and check out the PR branch:

   ```bash
   git clone https://github.com/vertical-cloud-lab/powder-doser
   cd powder-doser
   git checkout copilot/integrate-scale-feedback-loop
   ```

3. Install [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html),
   the CLI counterpart of the MicroPico extension — this is what lets
   an *agent* upload and run code without clicking:

   ```bash
   pip install mpremote
   ```

4. Plug the Pico W in over USB and confirm it's visible:

   ```bash
   mpremote devs
   ```

   (Close MicroPico's terminal first — only one program can hold the
   serial port at a time.  If `main.py` is running, mpremote interrupts
   it automatically.)

## 2. The command loop the agent (or you) drives

All commands run from `hardware/test-module/firmware/`:

```bash
# Upload every module the firmware imports (the June 30 failure was a
# stale config.py on flash — always re-upload after editing anything):
mpremote mkdir :tests || true
mpremote cp config.py scale.py dosing.py tic.py drv2605.py main.py :
mpremote cp tests/_keypress.py tests/test_scale_contact.py :tests/

# Run the no-keypress contact probe (~8 s, plus ~5 s per scanned preset):
mpremote run tests/test_scale_contact.py

# One-liners for spot checks:
mpremote exec "import config; print(config.SCALE_BAUD, config.SCALE_UART_ID)"
mpremote exec "import os; print(os.listdir())"

# Interactive REPL (Ctrl-] to exit); Ctrl-D soft-resets into main.py:
mpremote repl
```

A working starting prompt for Claude Code, from the repo root:

> The A&D HR-100A balance on this bench isn't answering the Pico over
> RS-232 (contact test FAILs at every serial preset).  Read
> `hardware/test-module/firmware/tests/README.md` and
> `hardware/test-module/scale-integration-report.md` §6 for history.
> Use `mpremote` (docs in `BENCH_DEBUG.md`) to upload and run
> `tests/test_scale_contact.py`, form one hypothesis at a time, and
> when a hypothesis needs a wiring change or a multimeter reading,
> stop and ask me to do it, then re-test.

The agent can edit `config.py`/test scripts, re-upload, re-run, and
read the verdicts on its own; only wiring changes and meter readings
need human hands.

## 3. First experiment to run: the stacked isolation test

Per the PR thread, the highest-value next step is removing the
breadboard and every jumper from the fault list in one move:

1. Unplug the Waveshare Pico-2CH-RS232 module from its breadboard and
   the jumpers from the Pico.
2. Plug the module **directly onto the Pico** (its female header onto
   the Pico's pins), with the **USB-end markings on both boards
   aligned** — mirrored stacking swaps every pin.
3. Plug the scale's cable into either of the module's DB9s.
4. In `tests/test_scale_contact.py`, set `STACKED = True`, upload, run.
   Stacked, the module's channels land on real UARTs (ch0 = UART0
   GP0/GP1, ch1 = UART1 GP4/GP5) and the probe tries **both channels ×
   both serial presets** automatically.

Reading the result:

| Outcome | Meaning |
|---|---|
| PASS/answer on either channel | Module, DB9 cable, scale, and scale settings are all **good** — the fault was the jumper wiring / breadboard / channel jumpering.  Rebuild the jumper harness against README step 8 and re-run with `STACKED = False`. |
| Silent on both channels, every preset | The fault is in the module↔scale segment or the scale itself.  Do the two checks below. |

Two decisive checks if it's still silent (details in
[`tests/README.md`](tests/README.md)):

- **PRINT-key test**: press the balance's `PRINT` key on a stable
  display during the probe's listen window.  The balance transmits one
  frame with zero configuration — if the module's RXD LED doesn't even
  blink, the scale→module segment (DB9 cable / adapters) is broken.
- **Voltage test**: multimeter, DC volts, at the scale's connector —
  its TX pin idles at **−5…−9 V** vs signal ground.  No negative idle
  anywhere ⇒ the cable isn't landing on the scale's pins 2/3/5 at all.

Afterwards, set `STACKED = False` and re-upload — the full rig can't
run stacked (GP0/GP1 and GP4/GP5 belong to the I2C and Tic channels).

## 4. Later: unattended remote debugging over Tailscale SSH

For iterating without anyone at the bench, park a small Linux box next
to the rig and leave the Pico plugged into it:

1. **Hardware**: Raspberry Pi Zero 2 W / 4B / 5 with Raspberry Pi OS
   Lite (**64-bit**), on the lab Wi-Fi, Pico W on its USB port.
2. On the Pi: `curl -fsSL https://tailscale.com/install.sh | sh`, then
   `sudo tailscale up --ssh` and authenticate it into the same
   tailnet as your laptop (enable Tailscale SSH in the admin console's
   access controls if prompted).
3. From anywhere on the tailnet: `ssh pi@<pi-hostname>` — no port
   forwarding, no lab-network firewall changes.
4. Install `mpremote` on the Pi; everything in §2 works identically
   over that SSH session.  Run Claude Code on your laptop and let it
   execute the `ssh pi@… "mpremote …"` commands (on a Zero 2 W, 512 MB
   of RAM makes running the agent *on* the Pi itself a squeeze — the
   laptop-drives-SSH pattern is the comfortable one; a Pi 4B/5 can host
   Claude Code directly).

This turns the bench into something an agent can poke 24/7, with a
human needed only when a hypothesis requires moving a wire.

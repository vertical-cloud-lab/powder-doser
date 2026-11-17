# Headed browser automation on the test Pi

Set up on 10 Oct 2026 (PR #97), so an agent can drive a real, headed Chromium
with mouse automation from the Pi's residential IP (some sites block datacenter
IPs). The Pi is the only one on the tailnet: a Raspberry Pi Zero 2 W (415 MB RAM,
Debian 13 "trixie", arm64). Nothing here runs at boot or on a timer.

## What was installed

| What | How | Where |
|---|---|---|
| `chromium` 154, `chromium-driver`, `xvfb`, `xauth`, `xdotool`, `x11-utils` | `apt-get install --no-install-recommends`, downloads capped at 1.5 MB/s, run as a one-off `systemd-run` unit so an SSH drop could not interrupt dpkg (log: `/var/log/browser-stack-install.log`) | system |
| Playwright 1.63 and Selenium 4.51 | wheels downloaded on the GitHub runner, copied with `scp -l 12000` (1.5 MB/s), installed offline into a venv | `~/browser-automation/.venv` (195 MB) |
| Smoke tests | `smoke_test_selenium.py`, `smoke_test_playwright.py`, `run_smoke_test.sh` | `~/browser-automation/` |

The packages take about 0.6 GB and the venv 0.2 GB of the SD card; the apt download cache was cleared afterwards (24 GB free).

## Using it

```bash
cd ~/browser-automation
Xvfb :99 -screen 0 1280x800x16 -nolisten tcp &   # virtual display
export DISPLAY=:99
.venv/bin/python smoke_test_selenium.py           # or smoke_test_playwright.py
xdotool mousemove 400 300 click 1                 # OS-level mouse, if needed
kill %1                                           # stop Xvfb when done
```

**Gotcha: pass `--no-memcheck`.** `/usr/bin/chromium` is a Raspberry Pi OS wrapper
script. On boards with little RAM it opens a "low memory" dialog (`zenoty`) and waits
for a click, which shows up as a launch timeout in Playwright or "Chrome instance exited"
in Selenium. Pass `--no-memcheck` as a browser argument (the smoke tests do), or point
the driver at the real binary, `/usr/lib/chromium/chromium`.

## Measured on 10 Oct 2026

Both drivers work headed on Xvfb, loading example.com, moving the mouse onto its link
and saving a screenshot:

- Selenium with the distro chromedriver: browser up in 44 s, 65 s in total. Available
  memory never fell below 184 MB (415 MB total, plus about 400 MB of zram swap).
- Playwright 1.63 driving the system Chromium 154: browser up in 22 s, 88 s in total.

It is slow but usable for one tab at a time. Keep `--renderer-process-limit=1` and close the browser
when done.

There are no stored logins. Sites such as LinkedIn will still show a login wall.

## Removing it

```bash
sudo apt-get purge chromium chromium-common chromium-driver xvfb xdotool x11-utils && sudo apt-get autoremove
rm -rf ~/browser-automation
```

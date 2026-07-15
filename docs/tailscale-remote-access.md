# Remote access to the powder doser via Tailscale SSH

This procedure sets up a Raspberry Pi Zero 2 W as a remote-access gateway for
the powder doser. The Zero 2 W joins a [Tailscale](https://tailscale.com/)
tailnet and runs [Tailscale SSH](https://tailscale.com/kb/1193/tailscale-ssh),
so anyone on the tailnet can SSH into it from anywhere without port
forwarding. The Raspberry Pi Pico W that drives the powder-dosing hardware
(see [`hardware/test-module/firmware/main.py`](../hardware/test-module/firmware/main.py))
plugs into the Zero 2 W over USB, and its one-line-per-command serial REPL is
reached from the SSH session.

It follows the AC Training Lab's
[Tailscale setup guide](https://ac-training-lab.readthedocs.io/en/latest/tailscale-setup.html);
refer to that page for tailnet-wide details (ACLs, Windows hosts, OT-2, etc.).

```
your laptop ──(Tailscale SSH)──▶ RPi Zero 2 W ──(USB serial, /dev/ttyACM0)──▶ Pico W ──▶ doser actuators
```

## What you need

- Raspberry Pi Zero 2 W
- microSD card (8 GB or larger) and a way to flash it
- 5 V / 2.5 A power supply with micro-USB connector (into the port labelled **PWR IN**)
- micro-USB **OTG** adapter or OTG data cable (into the port labelled **USB**) to
  connect the Pico W's USB cable
- 2.4 GHz Wi-Fi credentials for the lab network (the Zero 2 W has no 5 GHz radio)
- A Tailscale account with access to the lab's tailnet (ask the tailnet admin
  for an invite)

## 1. Flash Raspberry Pi OS

1. Install the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Choose **Raspberry Pi Zero 2 W** as the device and **Raspberry Pi OS Lite
   (64-bit)** as the operating system (no desktop needed — this is a headless
   gateway).
3. Before writing, open the OS customisation settings (the gear icon /
   "Edit Settings") and set:
   - **Hostname**: something recognisable on the tailnet, e.g. `powder-doser`
   - **Username / password**: e.g. user `pi` and a strong password
   - **Wi-Fi**: the lab's 2.4 GHz SSID and password, and the correct wireless
     LAN country
   - **Enable SSH** (password authentication is fine for the first boot;
     Tailscale SSH takes over afterwards)
4. Write the image, insert the card into the Zero 2 W, and power it up. First
   boot takes a couple of minutes.

## 2. Get a first shell on the Pi

From a machine on the **same Wi-Fi network**:

```sh
ssh pi@powder-doser.local
```

If mDNS doesn't resolve, find the Pi's IP from your router's client list (or
run `hostname -I` on the Pi with a keyboard/monitor attached) and
`ssh pi@<ip-address>` instead. Physical access with a mini-HDMI adapter and
keyboard also works for this one-time step.

Then update the OS:

```sh
sudo apt update && sudo apt full-upgrade -y
```

## 3. Install Tailscale and enable Tailscale SSH

Per the [installation instructions](https://tailscale.com/kb/1347/installation)
(the one-liner works on Raspberry Pi OS Bookworm):

```sh
curl -fsSL https://tailscale.com/install.sh | sh
```

Bring the node up with Tailscale SSH enabled:

```sh
sudo tailscale up --ssh
```

This prints an authentication URL — open it in a browser and log in with the
account that belongs to the lab's tailnet. When it completes, verify with:

```sh
tailscale status
```

The Pi should now appear as `powder-doser` in the
[Tailscale admin console](https://login.tailscale.com/admin/machines).

## 4. Tailnet admin steps (once, in the admin console)

Following the [AC Training Lab conventions](https://ac-training-lab.readthedocs.io/en/latest/tailscale-setup.html):

1. **Tag the device.** In the admin console's Access Controls, make sure the
   tag exists and is owned by admins:

   ```jsonc
   "tagOwners": {
       "tag:tailscale-ssh": ["autogroup:admin"],
   },
   ```

   and that the SSH rule's destination includes it:

   ```jsonc
   "dst": ["tag:tailscale-ssh"],
   ```

   Then assign `tag:tailscale-ssh` to the `powder-doser` machine
   (machine row → ⋯ → *Edit ACL tags*).

2. **Disable key expiry** for the machine (machine row → ⋯ → *Disable key
   expiry*) so the Pi doesn't drop off the tailnet after the default expiry
   period. (Weigh the security trade-off — see the Tailscale docs on
   [key expiry](https://tailscale.com/kb/1028/key-expiry).)

## 5. SSH in from anywhere

On your own machine, install Tailscale, log in to the same tailnet, and:

```sh
ssh pi@powder-doser
```

Tailscale handles authentication and encryption; no passwords or public keys
need to be managed on the Pi. The full MagicDNS name
(`powder-doser.<tailnet-name>.ts.net`) also works, e.g. for VS Code
Remote-SSH — set the SSH username in VS Code's settings, connect a terminal
first, then attach VS Code, as described in the AC Training Lab guide.

## 6. Connect the Pico W and reach the doser REPL

1. Plug the Pico W's USB cable into the Zero 2 W's **USB** (data) port via the
   micro-USB OTG adapter. Leave the Pico's existing wiring to the doser
   actuators untouched — it is powered and controlled over this one USB cable.
2. On the Pi, confirm the Pico enumerated as a USB-CDC serial device:

   ```sh
   ls /dev/ttyACM*
   ```

   You should see `/dev/ttyACM0`.
3. Give your user serial access (once, then log out/in):

   ```sh
   sudo usermod -aG dialout $USER
   ```

4. Install [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html),
   the MicroPython remote tool:

   ```sh
   sudo apt install -y pipx
   pipx install mpremote
   pipx ensurepath
   ```

5. Attach to the Pico's REPL:

   ```sh
   mpremote connect /dev/ttyACM0 repl
   ```

   The firmware's command loop (see the
   [firmware docstring](../hardware/test-module/firmware/main.py)) reads
   one-line commands: `h` for help, `s` for state, `d` to dispense, `r <deg>`
   to rotate the auger, `v` to vibrate, `t` to tap, `a <deg>` / `p <preset>`
   for the servo, and `!` for emergency stop. Exit the REPL with `Ctrl-]`
   (then `Ctrl-D` on the Pico restarts `main.py` if you interrupted it with
   `Ctrl-C`).

   Alternatively any serial terminal works, e.g.
   `sudo apt install -y picocom` and `picocom -b 115200 /dev/ttyACM0`
   (exit with `Ctrl-A Ctrl-X`).

## Troubleshooting

- **Pi never joins Wi-Fi**: the Zero 2 W is 2.4 GHz only — double-check the
  SSID isn't 5 GHz-only, and that the wireless country was set in the Imager.
- **Which OS am I on?** `hostnamectl` or `cat /etc/os-release`; the board
  serial number is in `cat /proc/cpuinfo`.
- **`tailscale status` shows logged out**: re-run `sudo tailscale up --ssh`
  and re-authenticate; check key expiry in the admin console.
- **`ssh pi@powder-doser` refused from the tailnet**: confirm the machine has
  `tag:tailscale-ssh` and the tailnet ACLs include the SSH rule from step 4;
  confirm your own device is logged in to the same tailnet (`tailscale status`
  locally).
- **No `/dev/ttyACM0`**: make sure the Pico is plugged into the Zero 2 W's
  *data* USB port (the middle one, labelled **USB**), not **PWR IN**, and that
  the cable/adapter is a data-capable OTG one. `dmesg | tail` after plugging
  in should show a `ttyACM` line.
- **REPL prints nothing**: the firmware only prints in response to commands —
  type `h` and press Enter. If `main.py` crashed, `Ctrl-D` soft-reboots the
  Pico and re-runs it.

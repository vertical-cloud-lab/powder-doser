# Powder-doser Pi device notes

Changes made directly on the powder-doser Raspberry Pi (Zero 2 W) that do not live in
this repo, recorded here per CLAUDE.md so they can be reproduced or reverted. The Pi is
reached via Tailscale SSH; NetworkManager (`nmcli`) manages networking.

## 2026-07-23 — Wi-Fi profile changes and tooling (issue #132)

Attempted to move the Pi from the `byu-devices` Wi-Fi network to the `samphone` phone
hotspot. The saved `samphone` NetworkManager profile authenticated successfully (WPA
handshake completed, so the stored password is correct), but the phone never issued a
DHCP lease on two attempts (45 s and 90 s timeouts), and on a third attempt the hotspot
had stopped broadcasting entirely — consistent with the phone's hotspot auto-off /
sleep behavior. The Pi remained on `byu-devices` via an explicit fallback
(`nmcli con up samphone || nmcli con up byu-devices` run in a transient systemd unit so
it survives the SSH drop).

Persistent changes left in place:

- `samphone` profile: `connection.autoconnect-priority` raised `0 → 30` (above
  `byu-devices` at 20) so `samphone` wins at boot/reconnect when both are visible.
  Note NetworkManager does not switch away from an already-active connection, so an
  explicit `nmcli con up samphone` is still needed for a live switch.
- `samphone` profile: `ipv4.dhcp-timeout` set `0 (default 45 s) → 90` to tolerate slow
  hotspot DHCP.
- Installed `tcpdump` (via apt) for network diagnostics.

To retry the switch once the hotspot is confirmed on and awake, run on the Pi:

```bash
sudo systemd-run --collect sh -c 'nmcli con up samphone || nmcli con up byu-devices'
```

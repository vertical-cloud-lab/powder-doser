# Read-only FTPS access to the Bambu printers, through the doser Pi

The printers are on the lab LAN. The runner reaches them only through the doser Pi
(Tailscale SSH). Everything here is read-only: `LIST`, `SIZE`, `MDTM` and `RETR`.
Nothing is uploaded or printed, and no MQTT commands are sent.

* `ftps_common.py`: implicit FTPS on port 990. It includes the PR #23 fixes: TLS before
  the greeting, TLS 1.2 pinned, and the data channel reusing the control channel's TLS session.
* `run_on_pi.sh`: sends `<PRINTER>_IP`, `<PRINTER>_ACCESS_CODE` and the scripts to the Pi over
  the SSH session's stdin. Secrets never go on a command line or on disk.
* `list_storage.py`: lists the storage folders.
* `fetch_frames.py` + `unframe.py`: stream files back with a rate cap. The Pi is on shared
  Wi-Fi, so the cap is 1 MB/s by default.

```bash
./run_on_pi.sh H2D list_storage.py
printf 'PATHS = ["/timelapse/video_2026-10-07_01-11-34.mp4"]\nRATE = 1_000_000\n' > /tmp/paths.py
./run_on_pi.sh H2D /tmp/paths.py fetch_frames.py | python3 -I unframe.py /tmp/h2d_dl
```

Times in `LIST` and `MDTM` are UTC. H2D file names (`video_*`, `ipcam-record.*`) are
UTC+8.

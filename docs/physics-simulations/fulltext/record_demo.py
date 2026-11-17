#!/usr/bin/env python3
"""Screen-record one full-text read through the Pi, pointer included, as evidence of the browsing route.

Starts its own Xvfb display, records it with ffmpeg's x11grab (which draws the X cursor), and drives the same
headed Chrome as fetch_fulltexts.py: open an arXiv abstract page, move the pointer, click "View PDF", scroll.
Writes pi_browser_demo.mp4 and pi_browser_demo.gif next to this script.

Usage: ./pi_socks.sh && python record_demo.py
"""
from __future__ import annotations

import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch_fulltexts as ft  # noqa: E402

DISPLAY = ":97"
W, H = 1366, 900


def main() -> None:
    import imageio_ffmpeg
    from playwright.sync_api import sync_playwright

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    os.environ["DISPLAY"] = DISPLAY
    raw = HERE / "pi_browser_demo_raw.mp4"
    rec = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "x11grab", "-draw_mouse", "1", "-framerate", "10",
                            "-video_size", f"{W}x{H}", "-i", DISPLAY, "-c:v", "libx264", "-preset", "veryfast",
                            "-pix_fmt", "yuv420p", str(raw)], stdin=subprocess.PIPE)
    try:
        with sync_playwright() as pw:
            browser, ctx, page = ft.open_browser(pw)
            page.goto("https://arxiv.org/abs/1410.2886", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(2500)
            for _ in range(3):
                ft.human_move(page, random.uniform(250, 1000), random.uniform(180, 650))
                page.wait_for_timeout(600)
            link = page.locator("a.download-pdf").first
            ft.human_click(page, link)
            page.wait_for_timeout(9000)
            for _ in range(4):
                page.mouse.wheel(0, 500)
                page.wait_for_timeout(1200)
            page.wait_for_timeout(1500)
            browser.close()
    finally:
        rec.stdin.write(b"q")
        rec.stdin.flush()
        rec.wait(timeout=30)
        xvfb.terminate()
    mp4 = HERE / "pi_browser_demo.mp4"
    gif = HERE / "pi_browser_demo.gif"
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(raw), "-vf", "scale=960:-2", "-c:v", "libx264",
                    "-crf", "30", "-pix_fmt", "yuv420p", str(mp4)], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(raw), "-vf",
                    "fps=5,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse",
                    str(gif)], check=True)
    raw.unlink()
    print("wrote", mp4.name, mp4.stat().st_size, gif.name, gif.stat().st_size)


if __name__ == "__main__":
    main()

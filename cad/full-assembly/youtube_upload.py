"""Upload the presentation video to YouTube as an unlisted video.

YouTube's Data API only accepts uploads from an OAuth user account (a
service account cannot own a channel), so this needs three secrets for a
Google Cloud OAuth client that has the YouTube Data API v3 enabled:

    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN

The refresh token is minted once, interactively, with the
``https://www.googleapis.com/auth/youtube.upload`` scope (for example with
``google_auth_oauthlib.flow.InstalledAppFlow(...).run_local_server()``), by
whoever owns the channel the video should land on.

    pip install google-api-python-client google-auth
    python3 youtube_upload.py                       # -> prints the watch URL
    python3 youtube_upload.py --file x.mp4 --title "..." --privacy unlisted
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT = HERE / "renders" / "assembly_presentation_720p.mp4"
TITLE = "Powder doser: assembly and operation (CAD walkthrough)"
DESCRIPTION = ("Step-by-step assembly of the Vertical Cloud Lab powder doser, from the mounting board "
               "to the auger cap, followed by the doser working: the servo tilt, the stepper-driven "
               "auger and the solenoid tap.\n\n"
               "Rendered from the CAD in https://github.com/vertical-cloud-lab/powder-doser "
               "(cad/full-assembly/video.py).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--file", default=str(DEFAULT))
    ap.add_argument("--title", default=TITLE)
    ap.add_argument("--privacy", default="unlisted", choices=["unlisted", "private", "public"])
    args = ap.parse_args()

    missing = [k for k in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
               if not os.environ.get(k)]
    if missing:
        print("not uploaded: missing " + ", ".join(missing), file=sys.stderr)
        return 2

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(None, refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YOUTUBE_CLIENT_ID"],
                        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    req = yt.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": args.title, "description": DESCRIPTION, "categoryId": "28"},
              "status": {"privacyStatus": args.privacy, "selfDeclaredMadeForKids": False}},
        media_body=MediaFileUpload(args.file, mimetype="video/mp4", chunksize=4 * 1024 * 1024,
                                   resumable=True))
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%", flush=True)
    print(f"https://youtu.be/{resp['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

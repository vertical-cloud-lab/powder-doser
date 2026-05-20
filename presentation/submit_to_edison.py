"""Submit the wrap-up presentation to Edison `analysis` for review.

Fire-and-forget: upload files, create the task, print the task ID, exit.
We do NOT wait for the response — per the project conventions, the next
session will fetch the result.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

API_KEY = os.environ.get("EDISON_API_KEY")
if not API_KEY:
    sys.stderr.write("EDISON_API_KEY is not set; cannot submit.\n")
    sys.exit(2)

# Endpoint defaults to https://api.platform.edisonscientific.com (Stage.PROD)

PRESENTATION_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PRESENTATION_DIR / "assets"

# Upload slides + the image and video the issue specifically called out.
files_to_upload = [
    PRESENTATION_DIR / "slides.md",
    PRESENTATION_DIR / "slides.pdf",
    PRESENTATION_DIR / "slides.html",
    ASSETS_DIR / "final-print-on-ultimaker.jpg",
    ASSETS_DIR / "final-print-video.mp4",
    ASSETS_DIR / "initial-sketch.jpg",
]

QUERY = """\
Please review the attached project wrap-up presentation for the
`vertical-cloud-lab/powder-excavator` project (issue #17, PR #18).

The presentation is a Marp deck. The source is `slides.md`; built outputs
are `slides.pdf` and `slides.html`. Two key media items are also attached:
the final-print photo on the Ultimaker 3 Extended
(`final-print-on-ultimaker.jpg`) and the print video
(`final-print-video.mp4`). The early sketch is `initial-sketch.jpg`.

Context: the deck is meant to follow Jean-Luc Doumont's presentation
principles — title areas are message areas (full-sentence messages),
maximize signal-to-noise, reduce on-slide noise. Narrative goal: tell the
story of the project across all 9 issues / 9 PRs, highlight the
before/after of giving the coding agent CAD tools and explicit
instructions to *try* tools (PR #2 → PR #7 → PR #16), highlight Edison
Scientific's role (literature synthesis, design review, data_entry
upload), and end with the printed Archimedes-auger final design.

Please give concrete, slide-by-slide suggestions for improvement:

1. Are the message-titles actually full-sentence messages, or are any of
   them still topic-titles? Rewrite any that fall short.
2. Where can signal-to-noise be improved (text to remove, images to
   enlarge, redundant slides to merge)?
3. Is the before/after of giving the agent CAD tools landing as the
   central insight? If not, what's the minimal restructuring that fixes
   it?
4. Is Edison Scientific's contribution clearly framed (PaperQA3
   high-effort literature synthesis, the `data_entry` upload flow used
   for design review, surfacing build123d / Will It Print / Jubilee)?
5. Any factual issues, missing context, or claims that need softening
   based on the attached files?
6. Suggested cuts or additional slides given a target length of ~10
   minutes / ~12 slides.

Please return a numbered list keyed to slide indices in `slides.md`.
"""


def main() -> None:
    client = EdisonClient(api_key=API_KEY)

    data_uris: list[str] = []
    missing: list[Path] = [p for p in files_to_upload if not p.exists()]
    if missing:
        sys.stderr.write(
            "Refusing to submit: required files are missing:\n"
            + "".join(f"  - {p}\n" for p in missing)
        )
        sys.exit(2)

    for path in files_to_upload:
        uri = client.upload_file(
            file_path=path,
            name=path.name,
            description=f"powder-excavator wrap-up: {path.name}",
            tags=["powder-excavator", "wrap-up", "issue-17", "pr-18"],
        )
        print(f"uploaded {path.name} -> {uri}")
        data_uris.append(uri)

    if not data_uris:
        sys.stderr.write("Refusing to submit: nothing was uploaded.\n")
        sys.exit(2)

    task = TaskRequest(
        name=JobNames.ANALYSIS,
        query=QUERY,
        tags=["powder-excavator", "wrap-up", "issue-17", "pr-18"],
    )
    created = client.create_task(task_data=task, files=data_uris)
    print("task submitted:")
    print(created)


if __name__ == "__main__":
    main()

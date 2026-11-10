# Paper review meeting — 2026-09-01

Everything derived from the 92-minute powder-doser paper review meeting between
Sam Charles and Sterling Baird, recorded at <https://youtu.be/vZWPl0S0c_g>.

## Start here

| File | What it is |
|---|---|
| **[REVISION-SPEC.md](REVISION-SPEC.md)** | **The document to review and edit.** Every meeting decision merged with Sam's notes, PR #97/#149/#150 and the Edison reviews into one ordered work-list, with six open questions that need a human answer. Nothing in it has been implemented. |
| [MEETING-FEEDBACK.md](MEETING-FEEDBACK.md) | The evidence behind the spec: 128 timestamped feedback points, each with the corrected quote, the screen the speaker was looking at, and the resulting action. |
| [TRANSCRIPT-corrected.md](TRANSCRIPT-corrected.md) | The full corrected transcript, plus a glossary of the speech-to-text errors that were fixed. |

## Supporting material

- `screenshots/` — 222 frames at 128 moments, named `NN[a-c]_HH-MM-SS_slug.webp`.
  Where a remark depends on cursor position, three frames were captured 6 s apart;
  all three are in the folder, and the feedback log embeds the two or three that
  actually differ. Cropped to the shared-screen region only, so no participant's
  face is committed.
- `sources/` — the Teams VTT, the tactiq export, Sam's raw notes, and the video
  metadata.
- `tools/` — `parse_vtt.py` and `extract_frames.py` + `shots.tsv`, so the
  transcript and every screenshot can be regenerated from the video.

## Two notes on provenance

**Timestamps are exact.** The Teams VTT ends at `01:32:01` against a 5522 s video,
so transcript time, video time and `?t=` offsets are all the same clock (wall
clock minus 14:41:18). This is confirmed twice inside the recording: the request
that became PR #149 was typed at `00:01:20` during the jargon discussion, and the
request that became PR #150 at `00:18:56`, seconds after Sterling says "it's like
test protocols".

**The video has no comments and no captions.** `comment_count` is 0 and both the
`subtitles` and `automatic_captions` fields are empty (`sources/video_metadata.json`).
There was nothing to interleave from YouTube; the Teams and tactiq transcripts are
the only spoken record.

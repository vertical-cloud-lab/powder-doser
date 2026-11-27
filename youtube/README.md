# YouTube uploads (not wired up in this repo yet)

[`yt_service.py`](yt_service.py) is digital-alloy-lab's copy of byu-vcl's helper for the **BYU Vertical Cloud Lab** channel, plus a
`--no-notify` switch. It needs `YOUTUBE_UPLOAD_TOKEN_PICKLE_B64` (scopes `youtube.upload` + `youtube.readonly`: it can upload and
list, not edit or delete). **powder-doser doesn't have that secret in its `claude.yml` yet**, so the run of 2026-11-27 (PR #185) made
the v11 walkthrough but couldn't upload it.

To let a run here upload, as digital-alloy-lab's `CLAUDE.md` describes:

1. Mint the token into this repo from a byu-vcl checkout with `youtube/client_secret.json`, signing in as the lab account and picking
   **BYU Vertical Cloud Lab**:
   ```bash
   python -c "import sys; sys.path.insert(0, 'youtube'); import generate_youtube_token as g; g.REPO = 'vertical-cloud-lab/powder-doser'; sys.argv = ['g', '--profile', 'upload', '--to-github']; g.main()"
   ```
2. Add one line to the `env:` block of the `claude` job in `.github/workflows/claude.yml` on `main` (a run can't edit workflows):
   ```yaml
   YOUTUBE_UPLOAD_TOKEN_PICKLE_B64: ${{ secrets.YOUTUBE_UPLOAD_TOKEN_PICKLE_B64 }}
   ```

Then the walkthrough goes up with one command (public, subscribers not notified; the description and chapters are in
[`cad/chain-carousel-v11/walkthrough/`](../cad/chain-carousel-v11/walkthrough/)):

```bash
pip install -r youtube/requirements.txt
python youtube/yt_service.py upload cad/chain-carousel-v11/walkthrough/walkthrough_v11.mp4 \
    --title "Multi-doser chain carousel v11: a walkthrough" \
    --description-file cad/chain-carousel-v11/walkthrough/description.txt --no-notify
```

Captions: upload `walkthrough_v11.srt` in YouTube Studio (the upload token can't add captions). Never decode, print or commit the token.

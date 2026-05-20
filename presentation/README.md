# Project wrap-up presentation

Marp slides for the `powder-doser` project (issue #17, PR #18).

## Build

```bash
cd presentation
npm install
npx marp --html --allow-local-files slides.md -o slides.html
npx marp --pdf  --html --allow-local-files slides.md -o slides.pdf
```

## How to present (with the videos playing)

The embedded `<video>` only plays in the **HTML** build, not the PDF. Four
ways to drive the live deck:

1. **GitHub Pages** *(easiest — public URL, forward/back, videos play)* — a
   workflow at [`.github/workflows/pages.yml`](../.github/workflows/pages.yml)
   builds `slides.html` and publishes it to GitHub Pages on every push to
   `main` that touches `presentation/`. Once enabled
   (*Settings → Pages → Source: GitHub Actions*), the deck is served at:

   ```
   https://vertical-cloud-lab.github.io/powder-doser/
   ```

   Marp's HTML output is a self-contained Bespoke deck, so the served page
   already supports arrow-key navigation, <kbd>F</kbd> for fullscreen,
   <kbd>O</kbd> for overview, on-page touch swipes, and inline `<video>`
   playback. Anyone with the URL can present from any laptop or tablet.

2. **Browser, fullscreen, local file** — open `slides.html` in
   Chrome/Firefox, press <kbd>F11</kbd> for fullscreen, then arrow keys to
   advance. GIFs autoplay and loop in both HTML and PDF.
3. **Marp watch/server mode** — for editing while presenting, run

   ```bash
   npx marp --html --allow-local-files --server .
   ```

   then open <http://localhost:8080/slides.html>. Edits to `slides.md` reload
   live.
4. **Marp Preview / VS Code Marp extension** — opens the deck in a
   presenter-style window with speaker notes; `<video>` plays here too.

## Files

- [`slides.md`](slides.md) — source (Marp Markdown)
- [`slides.html`](slides.html) — built HTML deck (renders the embedded video)
- [`slides.pdf`](slides.pdf) — built PDF (the GIF slide preserves the motion)
- [`assets/`](assets) — images, GIFs, and the print video referenced by the slides

## Design principles

Slides follow Jean-Luc Doumont's principles:

- The **title area is the message area** — every slide title is a complete
  sentence stating the message of the slide.
- **Maximize signal-to-noise** — one image or one short list per slide; no
  decorative chrome; chartjunk avoided.
- Build-up ordering: problem → first attempt → pushback → fix → result →
  generalization → next steps.

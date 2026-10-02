# McMaster-Carr data for the fasteners

`parts.json` is what McMaster's own catalog says about each fastener in
`hardware.MCMASTER`: the table row for the exact part number (thread,
length, head diameter and height, threading; width and height for nuts),
the catalog page it was read from, and the family's product image. It was
read on 2 Oct 2026 by `../../mcmaster_fetch.py`-style browsing through the
doser Pi, without logging in (see the full-assembly README, "Fasteners").

Not committed (`.gitignore`), because McMaster's files come with no licence
to redistribute them and this repo is public:

- `img/`: the family product images. `parts.json` has each one's URL and
  SHA-256; `../../fastener_check.py` reads them from here.
- `<PN>.step`: McMaster's 3-D STEP files. None could be fetched on 2 Oct
  (product pages need a login). If you download them by hand, put them here
  and `hardware.py` uses them instead of the stand-ins.

# McMaster-Carr data for the fasteners

What McMaster's own catalog says about each fastener in `hardware.MCMASTER`.
It was read on 2 Oct 2026 by `../../mcmaster_fetch.py`, through the doser Pi
and without logging in (full-assembly README, "Fasteners"). Product pages
need a login now; the catalog tables don't.

- `catalog_rows.json`: the raw table row for every part number, with the
  table's header rows and the catalog URL it came from.
- `parts.json`: the same figures, parsed: thread, length, head diameter and
  height, and threading for screws; width and height for nuts. It also
  names the family image `../../fastener_check.py` shows next to each
  stand-in, with its URL and SHA-256.

Not committed (`.gitignore`), because McMaster's files come with no licence
to redistribute them and this repo is public:

- `img/`: the family product images. `python3 mcmaster_fetch.py --images`
  downloads the five that `parts.json` names and checks their hashes.
- `<PN>.step`: McMaster's 3-D STEP files. None could be fetched on 2 Oct,
  because product pages need a login. If you download them by hand, put them
  here and `hardware.py` uses them instead of the stand-ins.

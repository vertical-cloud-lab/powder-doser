"""One SOP runner per test (SPEC 1-10). Each module has NUMBER, NAME,
TITLE, add_args(parser) and run(ctx, args) -> (results, checks)."""

from . import density, drum, faraday, heap, humidity, orifice, plate, psd, spread, ucs

TESTS = (heap, density, plate, psd, orifice, humidity, drum, ucs, spread, faraday)

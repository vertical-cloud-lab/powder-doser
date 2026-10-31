# Edison status

The nine queries in [`run_queries.py`](run_queries.py) were written for this survey (31 Oct 2026) but could not
be sent: every login to `https://api.platform.edisonscientific.com/auth/login` with `EDISON_PLATFORM_API_KEY`
returned **HTTP 403 `{"detail":"Forbidden"}`**.

| UTC (2026-10-31) | Route | Result |
|---|---|---|
| 01:47 | runner, `edison-client` 0.18.0 `create_task` | 403 at `/auth/login` ("Failed to authenticate") |
| 01:47–02:02 | runner, same, with retries every 15–90 s | 403 every time; no task was created |
| 02:04 | runner, plain `httpx` POST to `/auth/login` | 403 `{"detail":"Forbidden"}` (server: Google Frontend) |
| 02:05 | through the doser Pi (residential IP) as SOCKS5 | 403 `{"detail":"Forbidden"}`, so it is not an IP block |
| 02:14 | runner, plain `httpx` | 403 |

`GET /` answers 401 "Missing auth header", so the service is up and the key itself is being refused (revoked,
expired, or out of quota). The last Edison task in this repo that succeeded was the mock review of 13–15 Oct
(`paper/optimization/mock_review/`, task `2a2e76ab`).

To send the queries once the key works:

```bash
cd docs/physics-simulations
python edison/run_queries.py dispatch    # records task ids in edison/_task_ids.json
python edison/run_queries.py wait        # one foreground call; polls every 2 min, then fetches
```

`fetch` writes `<key>.task.json` and `<key>.answer.md` for every task.

In place of Edison, the literature step used web search plus open-access full texts read in a headed browser
through the Pi ([`../fulltext/`](../fulltext/)).

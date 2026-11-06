# Runs on the Pi after ftps_common.py. Lists the printer storage folders (read-only).
f = open_ftps()
print("login OK", flush=True)
def lst(path):
    print(f"=== {path}", flush=True)
    try:
        rows = []
        f.retrlines(f"LIST {path}", rows.append)
        for r in rows:
            print(r, flush=True)
    except Exception as e:
        print("  ERR", type(e).__name__, str(e)[:200], flush=True)
lst("/")
for d in ("/cache", "/model", "/timelapse", "/image", "/logger", "/ipcam"):
    lst(d)
f.quit()

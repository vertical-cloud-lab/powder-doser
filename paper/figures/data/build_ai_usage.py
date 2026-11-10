#!/usr/bin/env python3
"""Count generative-AI agent activity per week for SI Fig. S3.

Two measures, both from the public record of this repository:

* Agent requests: comments and issue/pull-request descriptions written by a
  team member that address ``@copilot`` or ``@claude``, plus pull requests the
  Copilot coding agent opened when it was assigned an issue. Each starts one
  agent session.
* Commits: every commit on every branch, split by author into the two agents
  and people. Commits that were rebased onto another branch appear more than
  once in git; they are counted once, keyed on author, author date and subject.

Needs ``gh`` (authenticated) and a clone with all remote branches fetched.
Writes ai_usage_weekly.csv, which make_data_figures.py plots.

Usage:  python3 build_ai_usage.py
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPO = "vertical-cloud-lab/powder-doser"
MENTION = re.compile(r"@(copilot|claude)\b", re.IGNORECASE)


def gh_pages(path: str) -> list[dict]:
    out = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", f"{path}?per_page=100&state=all"],
        check=True, capture_output=True, text=True,
    ).stdout
    return [item for page in json.loads(out) for item in page]


def is_bot(user: dict | None) -> bool:
    return user is None or user.get("type") == "Bot" or user["login"].endswith("[bot]")


def agent_requests() -> pd.DataFrame:
    rows = []
    issues = gh_pages(f"repos/{REPO}/issues")
    comments = (gh_pages(f"repos/{REPO}/issues/comments")
                + gh_pages(f"repos/{REPO}/pulls/comments"))
    for item in issues + comments:
        if is_bot(item.get("user")):
            # The Copilot coding agent opens a pull request for each assigned issue.
            if "pull_request" in item and item["user"]["login"] == "Copilot":
                rows.append((item["created_at"], "copilot"))
            continue
        for agent in {m.lower() for m in MENTION.findall(item.get("body") or "")}:
            rows.append((item["created_at"], agent))
    return pd.DataFrame(rows, columns=["time", "who"])


def commits() -> pd.DataFrame:
    log = subprocess.run(
        ["git", "log", "--remotes", "--format=%an%x1f%aI%x1f%s"],
        check=True, capture_output=True, text=True, cwd=HERE,
    ).stdout
    rows = {tuple(line.split("\x1f")) for line in log.splitlines() if line}
    out = []
    for author, when, _subject in rows:
        a = author.lower()
        who = "copilot" if "copilot" in a else "claude" if "claude" in a else "people"
        out.append((when, who))
    return pd.DataFrame(out, columns=["time", "who"])


def weekly(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    t = pd.to_datetime(df["time"], utc=True, format="ISO8601").dt.tz_convert(None)
    week = t.dt.to_period("W-SUN").dt.start_time  # weeks start on Monday
    counts = pd.crosstab(week, df["who"]).add_prefix(prefix)
    counts.index.name = "week_start"
    return counts


def main() -> None:
    table = weekly(agent_requests(), "requests_").join(
        weekly(commits(), "commits_"), how="outer").fillna(0).astype(int)
    table = table.asfreq("7D", fill_value=0)
    table.to_csv(HERE / "ai_usage_weekly.csv")
    print(table.sum().to_string())
    print(f"wrote ai_usage_weekly.csv ({len(table)} weeks, "
          f"{table.index.min():%Y-%m-%d} to {table.index.max():%Y-%m-%d})")


if __name__ == "__main__":
    main()

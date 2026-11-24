#!/usr/bin/env python3
"""Read-only central health check. Failed step labels never authorize a public proposal."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from harvest_failures import api, category

PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def pages(endpoint, key, token):
    seen = {}
    page = 1
    while True:
        separator = "&" if "?" in endpoint else "?"
        payload = api(endpoint + separator + urlencode({"per_page": 100, "page": page}), token)
        batch = payload[key]
        for entry in batch:
            seen[entry["id"]] = entry
        total = payload["total_count"]
        if len(seen) >= total:
            return list(seen.values())
        if len(batch) < 100 or page >= 10:
            raise RuntimeError("incomplete pagination")
        page += 1

def run():
    parser = argparse.ArgumentParser()
    # Preserve compatibility with the existing workflow, but never write this path.
    parser.add_argument("--output", type=Path, default=Path("docs/CANDIDATE_IMPROVEMENTS.md"))
    parser.add_argument("--days", type=int, default=14)
    args = parser.parse_args()
    if not 1 <= args.days <= 90:
        parser.error("days must be in 1..90")
    token = os.environ.get("HARNESS_SOURCE_READ_TOKEN", "")
    source = os.environ.get("HARNESS_PRIVATE_SOURCES", "")
    if not token or not source:
        print("SKIPPED: private source configuration unavailable; no evidence checked.")
        return 0
    repos = list(dict.fromkeys(x.strip() for x in source.split(",") if x.strip()))
    if not repos or any(not PATTERN.fullmatch(x) for x in repos):
        print("ERROR: invalid repository selector configuration.")
        return 1
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat(timespec="seconds").replace("+00:00", "Z")
    grouped = Counter()
    try:
        for repo in repos:
            endpoint = "/repos/" + repo
            runs = pages(endpoint + "/actions/runs?" + urlencode({"status": "failure", "created": ">=" + cutoff}), "workflow_runs", token)
            for run in runs:
                attempt = run.get("run_attempt") or 1
                jobs = pages(endpoint + "/actions/runs/" + str(run["id"]) + "/attempts/" + str(attempt) + "/jobs", "jobs", token)
                for job in jobs:
                    if job.get("conclusion") == "failure":
                        for step in job.get("steps", []):
                            if step.get("conclusion") == "failure":
                                grouped[category((job.get("name") or "") + " " + (step.get("name") or ""))] += 1
    except Exception:
        # No private identifiers, counts, error bodies or logs in public workflow output.
        print("ERROR: private metadata check incomplete; no candidate generated.")
        return 1
    # No category counts, private paths, or generated candidate text reach the public workflow.
    print("Metadata check complete. Step names are not root-cause evidence; no public candidate generated.")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())

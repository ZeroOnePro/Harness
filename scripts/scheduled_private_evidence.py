#!/usr/bin/env python3
"""Collect evidence in the calling private repository's trusted scheduled workflow.

Raw logs are temporary, never printed or uploaded. Only the private repository's
own workflow token is used. The artifact is an inventory, not a diagnosis.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from private_evidence_audit import REPO, EvidenceUnavailable, collect, gh, write_private


def check_context(env):
    repo = env.get("GITHUB_REPOSITORY", "")
    if (env.get("GITHUB_ACTIONS") != "true" or
            env.get("GITHUB_EVENT_NAME") not in ("schedule", "workflow_dispatch") or
            not REPO.fullmatch(repo) or not env.get("GH_TOKEN")):
        raise EvidenceUnavailable("trusted_private_schedule_required")
    meta = gh("/repos/" + repo)
    if meta.get("private") is not True:
        raise EvidenceUnavailable("private_repository_required")
    default = meta.get("default_branch")
    if not default or env.get("GITHUB_REF") != "refs/heads/" + default:
        raise EvidenceUnavailable("default_branch_required")
    temp = env.get("RUNNER_TEMP")
    if not temp or not Path(temp).is_dir():
        raise EvidenceUnavailable("runner_temp_required")
    return repo, Path(temp)


def inventory(report):
    """Explicit allowlist: no raw logs, source text, record text or log paths."""
    runs = []
    for run in report["runs"]:
        jobs = []
        for job in run["jobs"]:
            jobs.append({
                "id": job["id"],
                "log_collected": "log" in job,
                "signature": job.get("signature"),
                "signature_status": job.get("signature_status", "unavailable"),
            })
        runs.append({
            "id": run["id"], "attempt": run.get("run_attempt") or 1,
            "head_sha": run.get("head_sha"), "event": run.get("event"),
            "created_at": run.get("created_at"), "jobs": jobs,
        })
    return {
        "schema_version": 1,
        "collection_status": report["status"],
        "analysis_status": "requires_private_review",
        "failure_records": report.get("local_records", "unavailable"),
        "limitations": report["limitations"],
        "runs": runs,
        "counts": {
            "failed_runs": len(runs),
            "failed_jobs": sum(len(run["jobs"]) for run in runs),
            "logs_collected": sum(job["log_collected"] for run in runs for job in run["jobs"]),
            "unclassified_logs": sum(job["log_collected"] and not job["signature"]
                                     for run in runs for job in run["jobs"]),
        },
    }


def execute(env):
    repo, temp = check_context(env)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat(
        timespec="seconds").replace("+00:00", "Z")
    # Raw evidence is deleted even if collection fails.
    with tempfile.TemporaryDirectory(prefix="harness-raw-", dir=temp) as directory:
        report = inventory(collect(repo, cutoff, Path(directory)))
    report["cutoff_utc"] = cutoff
    write_private(temp / "harness-evidence.json",
                  (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print("Private evidence collection:", report["collection_status"], report["counts"])
    print("Root-cause review required; no public proposal or merge was made.")
    return 0 if report["collection_status"] == "complete" else 2


class Tests(unittest.TestCase):
    def test_requires_trusted_private_default_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "schedule",
                   "GITHUB_REPOSITORY": "example/project", "GH_TOKEN": "synthetic",
                   "GITHUB_REF": "refs/heads/main", "RUNNER_TEMP": tmp}
            with patch(__name__ + ".gh", return_value={"private": False}):
                with self.assertRaisesRegex(EvidenceUnavailable, "private_repository_required"):
                    check_context(env)
            with patch(__name__ + ".gh", return_value={"private": True, "default_branch": "main"}):
                self.assertEqual(check_context(env), ("example/project", Path(tmp)))
                with self.assertRaisesRegex(EvidenceUnavailable, "default_branch_required"):
                    check_context(dict(env, GITHUB_REF="refs/heads/other"))
            with patch(__name__ + ".gh") as mock:
                with self.assertRaisesRegex(EvidenceUnavailable, "trusted_private_schedule_required"):
                    check_context(dict(env, GITHUB_EVENT_NAME="pull_request"))
                mock.assert_not_called()

    def test_inventory_is_not_raw_evidence(self):
        report = {"status": "complete", "local_records": "collected", "limitations": [],
                  "secret_text": "NOT_PUBLIC", "runs": [
                      {"id": 1, "name": "NOT_PUBLIC", "run_attempt": 2, "jobs": [
                          {"id": 3, "name": "NOT_PUBLIC", "steps": ["NOT_PUBLIC"],
                           "log": "NOT_PUBLIC", "signature": "synthetic", "signature_status": "candidate_requires_review"}]}]}
        out = inventory(report)
        self.assertNotIn("NOT_PUBLIC", json.dumps(out))
        self.assertEqual(out["counts"]["logs_collected"], 1)
        self.assertEqual(out["analysis_status"], "requires_private_review")

    def test_raw_removed_and_partial_is_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "schedule",
                   "GITHUB_REPOSITORY": "example/project", "GH_TOKEN": "synthetic",
                   "GITHUB_REF": "refs/heads/main", "RUNNER_TEMP": tmp}
            def fake(repo, cutoff, directory):
                write_private(directory / "raw.log", b"NOT_PUBLIC")
                return {"status": "partial", "limitations": [], "runs": []}
            with patch(__name__ + ".gh", return_value={"private": True, "default_branch": "main"}), \
                    patch(__name__ + ".collect", side_effect=fake):
                self.assertEqual(execute(env), 2)
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["harness-evidence.json"])
            self.assertNotIn("NOT_PUBLIC", (Path(tmp) / "harness-evidence.json").read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    try:
        return execute(os.environ)
    except (EvidenceUnavailable, OSError, ValueError, KeyError, TypeError):
        # Never log exceptions containing private identifiers or raw data.
        print("Private scheduled evidence collection blocked or incomplete.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

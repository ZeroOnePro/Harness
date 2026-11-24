#!/usr/bin/env python3
"""Local, read-only Actions evidence collector. Never publishes evidence or opens PRs."""
import argparse
import base64
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from urllib.parse import urlencode
from unittest.mock import patch

REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ERROR = re.compile(r"(AssertionError|AssertionFailedError|FileNotFoundError|RuntimeError|TypeError|ValueError|ModuleNotFoundError|PermissionError|SyntaxError|ImportError|FAILED\b|##\[error\])")
STAMP = re.compile(r"^\d{4}-\d\d-\d\dT\S+\s+")
ANSI = re.compile(r"\x1b\[[0-9;]*m")

class EvidenceUnavailable(Exception):
    pass

def gh(endpoint, pages=False, raw=False):
    cmd = ["gh", "api", "--hostname", "github.com", endpoint]
    if pages:
        cmd += ["--paginate"]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise EvidenceUnavailable("cli_unavailable") from None
    if result.returncode:
        # Do not echo stderr: it may include private identifiers.
        status = re.search(rb"HTTP (\d{3})", result.stderr)
        if status:
            reason = "http_" + status.group(1).decode()
        elif b"unknown flag" in result.stderr.lower():
            reason = "unsupported_cli_option"
        elif b"gh auth login" in result.stderr.lower():
            reason = "authentication_required"
        else:
            reason = "request_failed"
        raise EvidenceUnavailable(reason)
    if raw:
        return result.stdout
    try:
        if pages:
            return decode_pages(result.stdout)
        return json.loads(result.stdout)
    except (ValueError, UnicodeError):
        raise EvidenceUnavailable("invalid_response") from None

def decode_pages(data):
    """Older gh versions emit consecutive JSON objects without an outer array."""
    source = data.decode("utf-8")
    decoder = json.JSONDecoder()
    pages = []
    index = 0
    while index < len(source):
        while index < len(source) and source[index].isspace():
            index += 1
        if index == len(source):
            break
        page, index = decoder.raw_decode(source, index)
        if not isinstance(page, dict):
            raise ValueError("expected JSON object page")
        pages.append(page)
    return pages

def items(endpoint, key):
    pages = gh(endpoint, pages=True)
    if not isinstance(pages, list) or not pages:
        raise EvidenceUnavailable("invalid_pages")
    result = {}
    total = pages[0].get("total_count")
    for page in pages:
        if not isinstance(page.get(key), list):
            raise EvidenceUnavailable("invalid_page")
        for item in page[key]:
            result[item["id"]] = item
    if not isinstance(total, int) or len(result) < total:
        raise EvidenceUnavailable("incomplete_pagination")
    return list(result.values())

def fingerprint(log):
    lines = []
    for raw in log.decode("utf-8", errors="replace").splitlines():
        line = STAMP.sub("", ANSI.sub("", raw)).strip()
        if len(line) <= 800 and ERROR.search(line) and not line.startswith("##[error]Process completed"):
            lines.append(line)
    if not lines:
        return None
    return hashlib.sha256("\n".join(sorted(set(lines))).encode()).hexdigest()

def write_private(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)

def collect(repo, cutoff, directory):
    result = {"repository": repo, "status": "complete", "runs": [], "limitations": []}
    prefix = "/repos/" + repo
    def limit(stage, exc):
        result["status"] = "partial"
        result["limitations"].append({"stage": stage, "reason": str(exc)})
    try:
        meta = gh(prefix)
        if meta.get("private") is not True:
            raise EvidenceUnavailable("private_repository_required")
    except EvidenceUnavailable as exc:
        limit("repository", exc)
        return result
    try:
        query = urlencode({"status": "failure", "created": ">=" + cutoff, "per_page": 100})
        runs = items(prefix + "/actions/runs?" + query, "workflow_runs")
    except EvidenceUnavailable as exc:
        limit("runs", exc)
        return result
    for run in runs:
        row = {k: run.get(k) for k in ("id", "name", "event", "head_sha", "created_at", "run_attempt")}
        row["jobs"] = []
        result["runs"].append(row)
        attempt = run.get("run_attempt") or 1
        try:
            jobs = items(prefix + "/actions/runs/" + str(run["id"]) + "/attempts/" + str(attempt) + "/jobs?per_page=100", "jobs")
        except EvidenceUnavailable as exc:
            limit("jobs", exc)
            continue
        for job in jobs:
            if job.get("conclusion") != "failure":
                continue
            entry = {"id": job["id"], "name": job.get("name"),
                     "steps": [s.get("name") for s in job.get("steps", []) if s.get("conclusion") == "failure"],
                     "status": "requires_private_review"}
            row["jobs"].append(entry)
            try:
                raw = gh(prefix + "/actions/jobs/" + str(job["id"]) + "/logs", raw=True)
                if not raw.strip():
                    raise EvidenceUnavailable("empty_log")
                logname = str(run["id"]) + "-" + str(job["id"]) + ".log"
                write_private(directory / logname, raw)
                entry["log"] = logname
                entry["signature"] = fingerprint(raw)
                if not entry["signature"]:
                    limit("signature", EvidenceUnavailable("no_specific_error_signal"))
            except EvidenceUnavailable as exc:
                limit("log", exc)
        if not row["jobs"]:
            limit("jobs", EvidenceUnavailable("no_failed_job_found"))
    try:
        record = gh(prefix + "/contents/.harness/failure-cases.jsonl")
        data = base64.b64decode(record["content"], validate=False)
        for line in data.decode("utf-8").splitlines():
            if line.strip():
                if not isinstance(json.loads(line), dict):
                    raise ValueError("record is not an object")
        write_private(directory / "failure-cases.jsonl", data)
        result["local_records"] = "collected"
    except EvidenceUnavailable as exc:
        result["local_records"] = "not_found_or_not_authorized" if str(exc) == "http_404" else "unavailable"
        if str(exc) != "http_404":
            limit("local_records", exc)
    except (KeyError, TypeError, ValueError, UnicodeError):
        result["local_records"] = "invalid"
        limit("local_records", EvidenceUnavailable("invalid_record"))
    return result

class Tests(unittest.TestCase):
    def test_legacy_cli_pagination(self):
        data = b'{"total_count":2,"jobs":[{"id":1}]}{"jobs":[{"id":2}]}\n'
        completed = subprocess.CompletedProcess([], 0, stdout=data, stderr=b"")
        with patch(__name__ + ".subprocess.run", return_value=completed) as execute:
            self.assertEqual(len(items("/example", "jobs")), 2)
            self.assertEqual(execute.call_args.args[0],
                             ["gh", "api", "--hostname", "github.com", "/example", "--paginate"])

    def test_cli_errors_are_safe(self):
        for code, message, expected in [
            (1, b"unknown flag: --example", "unsupported_cli_option"),
            (1, b"HTTP 403 private detail", "http_403"),
            (0, b"", "invalid_response"),
        ]:
            completed = subprocess.CompletedProcess([], code, stdout=b'{"jobs":', stderr=message)
            with patch(__name__ + ".subprocess.run", return_value=completed):
                with self.assertRaisesRegex(EvidenceUnavailable, "^" + expected + "$"):
                    gh("/example", pages=True)

    def test_pagination(self):
        with patch(__name__ + ".gh", return_value=[{"total_count": 2, "jobs": [{"id": 1}]}, {"jobs": [{"id": 2}]}]):
            self.assertEqual(len(items("example", "jobs")), 2)
        with patch(__name__ + ".gh", return_value=[{"total_count": 2, "jobs": [{"id": 1}]}]):
            with self.assertRaises(EvidenceUnavailable):
                items("example", "jobs")

    def test_signature(self):
        self.assertEqual(fingerprint(b"2025-01-01T00:00:00Z FileNotFoundError: fixture"),
                         fingerprint(b"2025-01-02T00:00:00Z FileNotFoundError: fixture"))
        self.assertIsNone(fingerprint(b"##[error]Process completed with exit code 1"))
        self.assertNotEqual(fingerprint(b"FileNotFoundError: fixture"), fingerprint(b"TypeError: fixture"))

    def test_private_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch(__name__ + ".gh", return_value={"private": False}) as mock:
                result = collect("example/project", "2025-01-01", Path(tmp))
                self.assertEqual(result["status"], "partial")
                self.assertEqual(mock.call_count, 1)
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_evidence_and_missing_record(self):
        def fake(endpoint, pages=False, raw=False):
            if endpoint.endswith("/contents/.harness/failure-cases.jsonl"):
                raise EvidenceUnavailable("http_404")
            if raw:
                return b"FileNotFoundError: fixture"
            if "/attempts/" in endpoint:
                return [{"total_count": 1, "jobs": [{"id": 2, "conclusion": "failure", "steps": []}]}]
            if "/actions/runs?" in endpoint:
                return [{"total_count": 1, "workflow_runs": [{"id": 1, "event": "push", "run_attempt": 2}]}]
            return {"private": True}
        with tempfile.TemporaryDirectory() as tmp:
            with patch(__name__ + ".gh", side_effect=fake):
                result = collect("example/project", "2025-01-01", Path(tmp))
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["local_records"], "not_found_or_not_authorized")
            self.assertTrue(result["runs"][0]["jobs"][0]["signature"])
            self.assertEqual((Path(tmp) / "1-2.log").stat().st_mode & 0o777, 0o600)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos", nargs="+")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        parser.error("private evidence collection is local-only")
    if not args.repos or any(not REPO.fullmatch(r) for r in args.repos) or not 1 <= args.days <= 90:
        parser.error("provide valid repositories and days in 1..90")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat(timespec="seconds").replace("+00:00", "Z")
    # Never place raw logs inside a source checkout or workflow artifact.
    root = Path(tempfile.mkdtemp(prefix="harness-private-", dir="/tmp"))
    reports = []
    for index, repo in enumerate(dict.fromkeys(args.repos), 1):
        directory = root / str(index)
        directory.mkdir(mode=0o700)
        reports.append(collect(repo, cutoff, directory))
    counts = Counter()
    for report in reports:
        for run in report["runs"]:
            for job in run["jobs"]:
                if job.get("signature"):
                    counts[job["signature"]] += 1
    summary = {"repositories": len(reports), "failed_runs": sum(len(r["runs"]) for r in reports),
               "failed_jobs_with_logs": sum("log" in j for r in reports for run in r["runs"] for j in run["jobs"]),
               "repeated_signatures": sum(n >= 2 for n in counts.values()),
               "partial_repositories": sum(r["status"] != "complete" for r in reports),
               "missing_or_unavailable_failure_records": sum(r.get("local_records") != "collected" for r in reports)}
    write_private(root / "report.json", json.dumps({"summary": summary, "repositories": reports}, ensure_ascii=False, indent=2).encode())
    print(json.dumps(summary))
    for index, report in enumerate(reports, 1):
        for entry in report["limitations"]:
            print(f'Repository {index}: {entry["stage"]}: {entry["reason"]}')
    print("Private evidence directory:", root)
    print("Review source at recorded commit and reproduce failures before proposing generic evals. Never share the private directory.")
    return 2 if summary["partial_repositories"] else 0

if __name__ == "__main__":
    raise SystemExit(main())

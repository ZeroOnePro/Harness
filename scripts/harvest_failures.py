#!/usr/bin/env python3
"""Collect PRIVATE repo's own failed Actions step metadata; never fetch raw logs."""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
import urllib.error


def api(path, token):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ZeroOnePro-Harness-Audit",
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def category(label):
    s = label.lower()
    for name, fragments in [
        ("test_regression", ("test", "pytest", "unittest", "jest", "gradle test", "vitest", "검증")),
        ("build_failure", ("build", "compile", "tsc", "lint", "typecheck", "bundl")),
        ("dependency_environment", ("install", "setup", "dependency", "cache", "checkout")),
        ("security_permission", ("permission", "auth", "secret", "token", "credential")),
        ("deployment", ("deploy", "release", "publish", "package")),
    ]:
        if any(word in s for word in fragments):
            return name
    return "unclassified"


def recommendation(kind):
    return {
        "test_regression": "재현 가능한 실패 테스트를 먼저 추가하고 수정 후 정상 사례를 재검증",
        "build_failure": "최초 실패 단계와 사용한 런타임·빌드 명령을 동일 조건으로 재현",
        "dependency_environment": "의존성 버전·실행 환경을 고정하고 환경 문제와 코드 문제를 구별",
        "security_permission": "권한 범위와 토큰 유무만 확인; 값이나 인증 로그를 공유하지 않음",
        "deployment": "빌드·패키징 결과와 실제 배포·기기 동작을 분리해 확인",
        "unclassified": "해당 비공개 저장소에서 실패 단계의 실제 근거를 검토해 분류 보완",
    }[kind]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--output", type=Path, default=Path("harness-failures.json"))
    args = parser.parse_args()
    token = os.getenv("GH_TOKEN", "")
    report = {"repository": args.repo, "scope": "private: workflow / job / failed step metadata only",
              "period_days": args.days, "status": "ok", "cases": [], "counts": {}, "limitations": []}
    if not args.repo or not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        report["status"] = "unavailable"
        report["limitations"].append("valid repository not provided")
    elif not token:
        report["status"] = "unavailable"
        report["limitations"].append("GH_TOKEN not available; no cross-repository access attempted")
    else:
        threshold = datetime.now(timezone.utc) - timedelta(days=args.days)
        try:
            runs = api(f"/repos/{args.repo}/actions/runs?status=failure&per_page=50", token).get("workflow_runs", [])
            for run in runs:
                timestamp = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                if timestamp < threshold:
                    continue
                jobs = api(f"/repos/{args.repo}/actions/runs/{run['id']}/jobs?per_page=100", token).get("jobs", [])
                for job in jobs:
                    if job.get("conclusion") != "failure":
                        continue
                    for step in job.get("steps", []):
                        if step.get("conclusion") != "failure":
                            continue
                        kind = category((job.get("name") or "") + " " + (step.get("name") or ""))
                        fingerprint = hashlib.sha256((args.repo + "|" + str(run.get("name")) + "|" + str(job.get("name"))
                                                      + "|" + str(step.get("name"))).encode()).hexdigest()[:16]
                        report["cases"].append({
                            "id": fingerprint, "category": kind, "run_id": run["id"],
                            "run_url": run.get("html_url"), "job": job.get("name"), "step": step.get("name"),
                            "observed_at": run.get("created_at"), "expected_check": recommendation(kind),
                            "status": "candidate_needs_reproduction",
                        })
            report["counts"] = dict(Counter(c["category"] for c in report["cases"]))
            report["limitations"].append("Step labels are only failure signals; actual root causes and tests require private evidence.")
            report["limitations"].append("First 50 failed runs and 100 jobs per run only; no raw logs or issue text.")
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
            report["status"] = "unavailable"
            report["limitations"].append("GitHub API failure: " + type(exc).__name__)
    # Optional evidence captured during local agent work stays in this PRIVATE project.
    local_cases = Path(".harness/failure-cases.jsonl")
    if local_cases.is_file():
        for line_number, line in enumerate(local_cases.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                sample = json.loads(line)
                if not isinstance(sample, dict) or not isinstance(sample.get("category"), str):
                    raise ValueError("category missing")
                kind = sample["category"]
                report["cases"].append({
                    "id": hashlib.sha256((args.repo + "|" + str(line_number) + "|" + line).encode()).hexdigest()[:16],
                    "category": kind, "source": "local_agent_failure", "status": "candidate_needs_reproduction",
                    "observed": sample.get("observed", ""), "expected": sample.get("expected", ""),
                    "regression": sample.get("regression", ""), "date": sample.get("date", ""),
                })
            except (ValueError, TypeError):
                report["limitations"].append(f"invalid local failure record line {line_number}")
    report["counts"] = dict(Counter(c["category"] for c in report["cases"]))
    repeats = [kind for kind, count in report["counts"].items() if count >= 2]
    report["improvement_candidates"] = [
        {"category": kind, "count": report["counts"][kind],
         "action": recommendation(kind) if kind in ("test_regression", "build_failure", "dependency_environment",
                                                    "security_permission", "deployment", "unclassified")
                   else "최초 실패 지점과 정상 사례를 같은 조건으로 재현하고 최소 하네스 변경 후보를 평가"}
        for kind in repeats
    ]
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Harness failure collection:", report["status"], report["counts"], report["limitations"])
    summary = Path(os.getenv("GITHUB_STEP_SUMMARY", ""))
    if str(summary) != ".":
        with summary.open("a", encoding="utf-8") as f:
            f.write("## Harness private failure audit\n\n" + json.dumps(report["counts"], ensure_ascii=False) +
                    "\n\nDetailed candidate data is retained only in the calling repository's workflow artifact.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

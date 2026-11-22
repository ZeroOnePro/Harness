#!/usr/bin/env python3
"""Opt-in cross-repository failed-step triage. Outputs ONLY generic categories."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import re
import sys
from harvest_failures import api, category, recommendation

PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GENERIC = {
    "test_regression": "실패한 테스트와 기존 정상 사례를 함께 재현하고 완료 기준을 강화한다.",
    "build_failure": "최초 실패한 빌드 단계와 실행 환경을 고정하고 같은 조건으로 재검증한다.",
    "dependency_environment": "도구·의존성 버전을 기록하고 환경 문제와 구현 오류를 분리한다.",
    "security_permission": "실제 인증·권한 경계를 검사하고 비밀값을 공개 로그에 남기지 않는다.",
    "deployment": "패키지 생성과 실제 사용자 실행·배포 성공을 구별한다.",
    "unclassified": "실패 원인 분류가 불충분하다. 내부 저장소에서 실제 trace를 확인한 뒤 일반화한다.",
}


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("docs/CANDIDATE_IMPROVEMENTS.md"))
    parser.add_argument("--days", type=int, default=14)
    args = parser.parse_args()
    token = os.environ.get("HARNESS_SOURCE_READ_TOKEN", "")
    source = os.environ.get("HARNESS_PRIVATE_SOURCES", "")
    if not token or not source:
        print("DISABLED: configure HARNESS_SOURCE_READ_TOKEN and HARNESS_PRIVATE_SOURCES in Harness Actions secrets.")
        return 0
    repos = [x.strip() for x in source.split(",") if x.strip()]
    if not repos or any(not PATTERN.fullmatch(x) for x in repos):
        print("ERROR: invalid repository selector secret")
        return 1
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    grouped = Counter()
    for repo in repos:
        try:
            runs = api(f"/repos/{repo}/actions/runs?status=failure&per_page=50", token).get("workflow_runs", [])
            for run in runs:
                if datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) < cutoff:
                    continue
                jobs = api(f"/repos/{repo}/actions/runs/{run['id']}/jobs?per_page=100", token).get("jobs", [])
                for job in jobs:
                    if job.get("conclusion") != "failure":
                        continue
                    for step in job.get("steps", []):
                        if step.get("conclusion") == "failure":
                            grouped[category((job.get("name") or "") + " " + (step.get("name") or ""))] += 1
        except Exception as exc:
            # Deliberately avoid logging private repository names, URLs or error bodies.
            print("ERROR: private repository access failed:", type(exc).__name__)
            return 1
    recurring = sorted(key for key, count in grouped.items() if count >= 2)
    if not recurring:
        print("No repeated generic failure categories; no public candidate changes.")
        return 0
    body = ["# 하네스 개선 후보 (비식별 집계)", "",
            "비공개 저장소의 실패 로그·저장소명·실행 링크는 공개하지 않습니다.",
            "아래 항목은 실패한 Actions 단계 이름에서 추정한 **검증할 가설**입니다.",
            "실제 원인 파악·수정 완료·Agent Evals 통과를 뜻하지 않습니다.", ""]
    for key in recurring:
        body.extend([f"## {key}", "", GENERIC[key], "",
                     "검증 계획: 동일한 실패·정상 사례를 실행하고, 한 요소만 변경해 회귀 여부를 비교한다.", "",
                     "상태: 후보 / 원인 미검증 / 자동 배포 금지", ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(body), encoding="utf-8")
    print(f"Generated generic improvement candidates: {len(recurring)} categories (no private details).")
    return 0


if __name__ == "__main__":
    sys.exit(run())

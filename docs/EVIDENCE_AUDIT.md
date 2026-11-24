# Evidence-first failure audit

The central scheduled check is metadata-only. It must not turn step names into public proposals. Missing configuration is a skip, not successful evidence collection. No existing security or permission rules are changed.

Run the local collector in a trusted Linux/WSL environment with Python 3, a recent GitHub CLI supporting `--paginate --slurp`, and an authenticated read-only connection (Actions and Contents read for the selected private repositories):

```sh
python3 scripts/private_evidence_audit.py --self-test
python3 scripts/validate_harness.py --mode central --output /tmp/harness-validation.json
gh auth status
python3 scripts/private_evidence_audit.py --days 14 --repos OWNER/PRIVATE_REPOSITORY
```

The collector queries failed runs across event types, paginates results, reads failed jobs for the latest attempt, and retrieves logs and optional committed failure records. It rejects public repositories and CI execution. The report and logs are created in a new local private temporary directory outside the checkout (directory mode 0700, files 0600). Do not upload, commit, paste or publish that directory. Delete it after private review. Local uncommitted records, successful reruns of previously failed attempts, expired logs and actual reproduction are outside the collection scope. A missing optional record cannot establish whether it is absent or unauthorized. Partial required evidence exits nonzero. Exact log signatures are triage hints, not root-cause identity.

Before a public change, review the failed commit, relevant implementation and tests privately; distinguish environment, test fixture and product defects. Reproduce the failure and a passing control. Compare the proposed generalized behavior with existing evaluation cases and open PRs. Only independently authored synthetic, non-identifying tests and guidance may be proposed in a separate review branch; never copy private evidence or its hashes. Do not automatically merge. Automated root-cause analysis, semantic deduplication and automatic publication are intentionally not provided by this collector.

The self-tests use synthetic fixtures, exercise pagination, missing optional records, local file permissions, signature stability and rejection of public repositories. Passing them does not prove live API access or downstream application behavior.

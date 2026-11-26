# Evidence-first failure audit

The central scheduled check validates public Harness files and synthetic tests only. Private scheduled evidence collection runs inside the calling private repository with its existing repository-scoped token; it never publishes proposals. No existing user security or permission rules are changed.

Run the local collector in a trusted Linux/WSL environment with Python 3, GitHub CLI supporting `--paginate` (including version 2.45.0; no `--slurp` required), and an authenticated read-only connection (Actions and Contents read for the selected private repositories):

```sh
python3 scripts/private_evidence_audit.py --self-test
python3 scripts/validate_harness.py --mode central --output /tmp/harness-validation.json
gh auth status
python3 scripts/private_evidence_audit.py --days 14 --repos OWNER/PRIVATE_REPOSITORY
```

The collector queries failed runs across event types, paginates results, reads failed jobs for the latest attempt, and retrieves logs and optional committed failure records. The local CLI rejects public repositories and CI execution. The separate scheduled entry point validates the private caller, default branch, event and token, and uploads only an allowlisted inventory in that repository. Scheduled log downloads use the repository-scoped token through the REST endpoint and follow HTTPS redirects without forwarding credentials outside the API origin. Metadata uses the existing CLI path. Local CLI behavior is unchanged. HTTP and transport failures are reported using safe error codes; a log exceeding the explicit 64 MiB per-job limit is incomplete, not silently truncated. Raw logs and failure records are deleted from the runner temporary directory. The report and logs are created in a new local private temporary directory outside the checkout (directory mode 0700, files 0600). Do not upload, commit, paste or publish that directory. Delete it after private review. Local uncommitted records, successful reruns of previously failed attempts, expired logs and actual reproduction are outside the collection scope. A missing optional record cannot establish whether it is absent or unauthorized. Partial required evidence exits nonzero. Exact log signatures are triage hints, not root-cause identity. A retrieved log without a specific signature is still collected evidence; the summary reports unmatched logs separately and root-cause review remains pending. A successful collector exit does not establish root cause.

Before a public change, review the failed commit, relevant implementation and tests privately; distinguish environment, test fixture and product defects. Reproduce the failure and a passing control. Compare the proposed generalized behavior with existing evaluation cases and open PRs. Only independently authored synthetic, non-identifying tests and guidance may be proposed in a separate review branch; never copy private evidence or its hashes. Do not automatically merge. Automated root-cause analysis, semantic deduplication and automatic publication are intentionally not provided by this collector.

The self-tests use synthetic fixtures, exercise legacy CLI argument and response compatibility, safe error diagnostics, separation of collected logs from unresolved signatures, pagination, missing optional records, local file permissions, signature stability and rejection of public repositories. Passing them does not prove live API access or downstream application behavior.

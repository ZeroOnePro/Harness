# AGENTS.md

## Goal
Work accurately while minimizing context size, tool calls, output, and unrelated changes.

## Repository Navigation
- Inspect only files relevant to the current task.
- Prefer targeted search (`rg`, symbol/file search) before reading files.
- If the target file or symbol is already known, start there.
- Read only the minimum surrounding code needed to make a safe change.
- Do not scan the entire repository unless the task genuinely requires it.
- Do not repeatedly read the same file unless it may have changed.
- Ignore generated, dependency, cache, build, and large log files unless directly relevant.

Commonly irrelevant paths: `node_modules/`, `dist/`, `build/`, `coverage/`, `.git/`, `.cache/`, `.next/`, `vendor/`, logs, source maps, minified files, and lockfiles.

## Editing
- Make the smallest safe change that satisfies the request.
- Do not refactor unrelated code.
- Do not rewrite an entire file when a small patch is sufficient.
- Preserve existing naming, formatting, architecture, and project conventions.
- Do not add abstractions, dependencies, helpers, comments, or configuration unless necessary.
- Do not modify unrelated formatting or files.
- Avoid speculative cleanup and premature optimization.

## Tool Usage
- Before each tool call, ask whether the current information is already sufficient.
- Stop exploring once the cause and safe modification point are clear.
- Prefer one focused search/read/edit/verify loop over repeated broad exploration.
- Keep command output small. Filter, grep, or tail large outputs instead of loading full logs.
- Do not print or inspect successful verbose output unless needed.

## Validation
Use the narrowest useful validation first:
1. targeted test
2. relevant package/module test
3. type/lint check
4. build
5. full test suite only when justified

Do not run expensive repository-wide validation for a small isolated change unless required by repository policy.

## Responses
- Keep progress and final explanations concise.
- Do not restate the user's request.
- Do not explain unchanged code.
- Report only what changed, important reason/constraint, validation result, and remaining issue, if any.
- If enough information exists, implement instead of continuing discussion.

## Priority
1. Correctness
2. Safety
3. Explicit user requirements
4. Repository instructions and conventions
5. Minimal change
6. Token/context efficiency

Never sacrifice correctness merely to save tokens.

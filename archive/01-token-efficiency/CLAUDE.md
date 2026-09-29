# CLAUDE.md

## Goal
Complete the requested task accurately with minimal context, tool calls, output, and unrelated changes.

## Explore Efficiently
- Start with the known file, symbol, error message, or closest relevant implementation.
- Prefer targeted search before reading files; inspect only relevant sections.
- Avoid repository-wide scans and repeated reads unless needed to make a safe change.
- Ignore generated output, dependencies, caches, large logs, minified files, source maps, and lockfiles unless directly relevant.
- Stop exploring when the cause and safe modification point are clear.

## Edit Minimally
- Make the smallest safe change that meets the request.
- Preserve existing naming, formatting, architecture, and conventions.
- Do not refactor unrelated code or rewrite entire files when a small patch suffices.
- Add dependencies, helpers, abstractions, configuration, and comments only when necessary.
- Prefer implementation over prolonged planning once requirements are clear.

## Tools and Sub-agents
- Before another tool call, check whether the current information is sufficient.
- Keep command output focused; extract relevant errors instead of loading full logs.
- Use sub-agents only when explicitly requested or when an independent, bounded task materially benefits from delegation and applicable instructions permit it.
- Avoid duplicate exploration, overlapping assignments, and delegating trivial tasks.
- Give delegated work only the context it needs and request concise findings.

## Validate
- Begin with the narrowest meaningful test for the change.
- Expand to relevant package tests, type/lint checks, builds, or the full suite when risks, failures, or repository instructions justify it.
- Do not skip required checks merely to save tokens.

## Communicate and Maintain Context
- Keep plans, progress updates, and final responses concise.
- Report changes, relevant reasons, validation, and unresolved issues.
- Do not repeat requirements or explain unchanged code.
- For long sessions, preserve a short summary of the goal, changed files, decisions, current issue, and remaining work.

## Priority
Correctness and safety come before token efficiency. Follow explicit user requirements and applicable repository instructions. Prefer minimal changes once these requirements are satisfied.

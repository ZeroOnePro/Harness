#!/usr/bin/env python3
"""Validate archived harness integrity and shared instructions, or a consumer project."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def central(root):
    errors, warnings = [], []
    manifest = json.loads((root / "attachments-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("attachment_count") != len(manifest.get("files", [])) or len(manifest["files"]) != 9:
        errors.append("attachment manifest must contain exactly nine originals")
    for item in manifest["files"]:
        path = root / item["path"]
        if not path.is_file():
            errors.append(f"missing original: {item['path']}")
            continue
        content = path.read_bytes()
        if len(content) != item["bytes"] or hashlib.sha256(content).hexdigest() != item["sha256"]:
            errors.append(f"original content changed: {item['path']}")
    targets = [root / "README.md", root / "AGENTS.md"]
    targets += list((root / "docs").rglob("*.md"))
    targets += list((root / ".agents" / "skills").rglob("SKILL.md"))
    for src in targets:
        for link in re.findall(r"\]\(([^)]+)\)", src.read_text(encoding="utf-8")):
            if "://" in link or link.startswith(("#", "mailto:")):
                continue
            link = link.split("#", 1)[0]
            if link and not (src.parent / link).exists():
                errors.append(f"broken relative reference {src.relative_to(root)}: {link}")
    for skill in (root / ".agents" / "skills").glob("*/SKILL.md"):
        body = skill.read_text(encoding="utf-8")
        if not body.startswith("---\n") or not re.search(rf"(?m)^name:\s*{re.escape(skill.parent.name)}\s*$", body):
            errors.append(f"invalid skill frontmatter: {skill}")
    if not (root / "shared" / "COMMON_RULES.md").is_file():
        errors.append("missing centrally managed shared rules")
    return errors, warnings


def project(root):
    errors, warnings = [], []
    agents = root / "AGENTS.md"
    if not agents.is_file():
        warnings.append("AGENTS.md missing: coding agents may not load common rules")
    else:
        text = agents.read_text(encoding="utf-8")
        if ".harness/COMMON_RULES.md" not in text:
            warnings.append("AGENTS.md does not reference .harness/COMMON_RULES.md")
    if not (root / ".harness" / "COMMON_RULES.md").is_file():
        warnings.append("shared rules absent; run project sync job")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--mode", choices=["central", "project"], required=True)
    parser.add_argument("--output", type=Path, default=Path("harness-validation.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    errors, warnings = central(root) if args.mode == "central" else project(root)
    result = {"mode": args.mode, "status": "fail" if errors else ("warn" if warnings else "pass"),
              "errors": errors, "warnings": warnings}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

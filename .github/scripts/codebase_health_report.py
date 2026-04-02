#!/usr/bin/env python3
"""Aggregate SwiftLint + tech-debt + security reports into a single health summary."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


def count_swift_loc(root: Path) -> tuple[int, int]:
    skip = {"Pods", "Carthage", "DerivedData", "DerivedDataCI", ".build", "build", ".git"}
    files = 0
    loc = 0
    for path in root.rglob("*.swift"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in skip for part in rel.parts):
            continue
        files += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        loc += sum(1 for line in text.splitlines() if line.strip())
    return files, loc


def swiftlint_summary(swiftlint_json: Path) -> tuple[str, Counter[str]]:
    if not swiftlint_json.is_file():
        return "SwiftLint report not found (run SwiftLint step first).", Counter()
    try:
        data = json.loads(swiftlint_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "SwiftLint JSON missing or invalid.", Counter()
    if not isinstance(data, list):
        return "SwiftLint JSON unexpected shape.", Counter()
    severities = Counter()
    for item in data:
        if isinstance(item, dict) and "severity" in item:
            severities[str(item["severity"]).lower()] += 1
        elif isinstance(item, dict):
            severities["unknown"] += 1
    total = sum(severities.values())
    parts = [f"Total violations: **{total}**"]
    for key in ("error", "warning"):
        if severities[key]:
            parts.append(f"- {key}: {severities[key]}")
    if severities:
        parts.append(f"- Other / unknown: {sum(v for k, v in severities.items() if k not in ('error', 'warning'))}")
    return "\n".join(parts), severities


def count_markdown_table_priorities(md_path: Path) -> Counter[str]:
    """Count data rows whose first column is P1 / P2 / P3."""
    counts: Counter[str] = Counter()
    if not md_path.is_file():
        return counts
    text = md_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        match_prio = re.match(r"^\|\s*(P[123])\b", line)
        if match_prio:
            counts[match_prio.group(1)] += 1
    return counts


def main() -> int:
    root = Path.cwd()
    reports = root / "Reports"
    reports.mkdir(parents=True, exist_ok=True)
    out_path = reports / "codebase-health-summary.md"

    sha = os.environ.get("GITHUB_SHA", "local")
    ref = os.environ.get("GITHUB_REF", "local")
    run_id = os.environ.get("GITHUB_RUN_ID", "n/a")

    swift_files, swift_loc = count_swift_loc(root)
    sl_text, sl_sev = swiftlint_summary(reports / "swiftlint.json")

    td_path = reports / "tech-debt.md"
    sec_path = reports / "security-findings.md"
    td_counts = count_markdown_table_priorities(td_path)
    sec_counts = count_markdown_table_priorities(sec_path)

    health_score = 100
    health_score -= min(40, sl_sev.get("error", 0) * 5)
    health_score -= min(30, sl_sev.get("warning", 0) * 2)
    health_score -= min(15, td_counts.get("P1", 0) * 3)
    health_score -= min(10, sec_counts.get("P1", 0) * 5)
    health_score = max(0, health_score)

    lines = [
        "# Codebase health check",
        "",
        f"- **Commit / ref:** `{sha[:7] if len(sha) > 7 else sha}` on `{ref}`",
        f"- **Workflow run:** `{run_id}`",
        "",
        "## Snapshot",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Swift files | {swift_files} |",
        f"| Swift non-blank LOC (approx) | {swift_loc} |",
        "",
        "## Heuristic health score",
        "",
        f"**{health_score} / 100** — derived from SwiftLint severities, P1 tech-debt markers, and P1 security heuristics (not a substitute for review).",
        "",
        "## SwiftLint",
        "",
        sl_text,
        "",
        "## Tech debt (marker counts by priority)",
        "",
        f"- P1: {td_counts.get('P1', 0)}",
        f"- P2: {td_counts.get('P2', 0)}",
        f"- P3: {td_counts.get('P3', 0)}",
        "",
        f"Details: see `tech-debt.md` in the same artifact bundle.",
        "",
        "## Security heuristics (by priority)",
        "",
        f"- P1: {sec_counts.get('P1', 0)}",
        f"- P2: {sec_counts.get('P2', 0)}",
        f"- P3: {sec_counts.get('P3', 0)}",
        "",
        f"Details: see `security-findings.md`. Consider enabling **CodeQL** and **Dependabot** for deeper coverage.",
        "",
        "## Artifacts",
        "",
        "Download the **ios-code-health-reports** artifact from this workflow run for full markdown + `swiftlint.json`.",
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

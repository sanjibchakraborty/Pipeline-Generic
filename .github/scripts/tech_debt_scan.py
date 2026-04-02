#!/usr/bin/env python3
"""Scan Swift sources for tech-debt markers; write markdown report with priorities."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    priority: str
    tag: str
    path: str
    line_no: int
    line: str


# Order: first match wins (more specific tags first).
PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bTECHDEBT\s*(\([^)]*\))?\s*:", re.I), "P1", "TECHDEBT"),
    (re.compile(r"\bFIXME\b"), "P1", "FIXME"),
    (re.compile(r"\bHACK\b"), "P1", "HACK"),
    (re.compile(r"\bXXX\b"), "P2", "XXX"),
    (re.compile(r"\bTODO\b"), "P2", "TODO"),
    (re.compile(r"\bOPTIMIZE\b"), "P3", "OPTIMIZE"),
    (re.compile(r"\bREFACTOR\b"), "P3", "REFACTOR"),
]

SKIP_DIRS = {"Pods", "Carthage", "DerivedData", "DerivedDataCI", ".build", "build", ".git"}


def should_skip(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in SKIP_DIRS for part in rel.parts)


def scan_file(path: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//") or "/*" in line or stripped.startswith("*"):
            pass
        for pattern, priority, tag in PATTERNS:
            if pattern.search(line):
                findings.append(
                    Finding(
                        priority=priority,
                        tag=tag,
                        path=str(path.relative_to(root)),
                        line_no=line_no,
                        line=line.strip()[:200],
                    )
                )
                break
    return findings


def main() -> int:
    root = Path.cwd()
    out_dir = root / "Reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "tech-debt.md"

    swift_files = [
        p
        for p in root.rglob("*.swift")
        if p.is_file() and not should_skip(p, root)
    ]
    all_findings: list[Finding] = []
    for swift_path in sorted(swift_files):
        all_findings.extend(scan_file(swift_path, root))

    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    all_findings.sort(key=lambda f: (priority_order.get(f.priority, 9), f.path, f.line_no))

    lines = [
        "# Tech debt scan",
        "",
        f"Swift files scanned: **{len(swift_files)}**",
        f"Markers found: **{len(all_findings)}**",
        "",
        "| Priority | Meaning |",
        "|----------|---------|",
        "| **P1** | Fix soon — correctness, hacks, explicit TECHDEBT/FIXME/HACK |",
        "| **P2** | Plan — TODO / XXX |",
        "| **P3** | Improve when touching code — OPTIMIZE / REFACTOR |",
        "",
    ]

    if not all_findings:
        lines.append("_No tech-debt markers detected in scanned Swift files._")
    else:
        lines.extend(["| Priority | Tag | Location | Snippet |", "|------------|-----|----------|---------|"])
        for f in all_findings:
            loc = f"{f.path}:{f.line_no}"
            snippet = f.line.replace("|", "\\|")
            lines.append(f"| {f.priority} | {f.tag} | `{loc}` | {snippet} |")

    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

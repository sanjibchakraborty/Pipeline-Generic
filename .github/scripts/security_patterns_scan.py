#!/usr/bin/env python3
"""
Heuristic security pattern scan for Swift/iOS sources (static, not a SAST replacement).
Flags common misconfigurations and risky patterns; review all findings manually.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    priority: str
    category: str
    path: str
    line_no: int
    line: str
    note: str


RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "P1",
        "ATS / transport security",
        re.compile(r"NSAllowsArbitraryLoads\s*[=:]\s*(true|YES)", re.I),
        "App Transport Security allows arbitrary loads — prefer HTTPS and exceptions per domain.",
    ),
    (
        "P1",
        "Hardcoded secret (suspected)",
        re.compile(
            r'(?i)(api[_-]?key|secret|password|token|bearer)\s*[=:]\s*["\'][^"\']{8,}["\']'
        ),
        "Possible hardcoded credential — use Keychain, xcconfig (gitignored), or secrets manager.",
    ),
    (
        "P2",
        "Debug print of sensitive keyword",
        re.compile(r"\bprint\s*\([^)]*(password|secret|token|apiKey)", re.I),
        "Avoid logging values near sensitive keywords; use conditional compilation or os_log redaction.",
    ),
    (
        "P2",
        "Insecure URL scheme in code",
        re.compile(r'["\']http://[^"\']+["\']'),
        "Plain HTTP URL — prefer https:// unless explicitly required and documented.",
    ),
    (
        "P2",
        "Disabled validation",
        re.compile(r"allowsArbitraryLoads|disableATS|NSURLSession.*delegate.*challenge", re.I),
        "Review certificate / challenge handling — ensure pinning or system validation where needed.",
    ),
    (
        "P3",
        "Force try / cast",
        re.compile(r"\btry!|\bas!"),
        "Force try/cast can crash; consider guard/if let for security-sensitive flows.",
    ),
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
        for priority, category, pattern, note in RULES:
            if pattern.search(line):
                findings.append(
                    Finding(
                        priority=priority,
                        category=category,
                        path=str(path.relative_to(root)),
                        line_no=line_no,
                        line=line.strip()[:200],
                        note=note,
                    )
                )
    return findings


def main() -> int:
    root = Path.cwd()
    out_dir = root / "Reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "security-findings.md"

    swift_files = [
        p
        for p in root.rglob("*.swift")
        if p.is_file() and not should_skip(p, root)
    ]
    plist_files = [
        p
        for p in root.rglob("*.plist")
        if p.is_file() and not should_skip(p, root) and "xcuserdata" not in str(p)
    ]

    all_findings: list[Finding] = []
    for swift_path in sorted(swift_files):
        all_findings.extend(scan_file(swift_path, root))

    # Info.plist ATS keys
    ats_pattern = re.compile(r"NSAllowsArbitraryLoads", re.I)
    for plist_path in sorted(plist_files):
        try:
            content = plist_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if ats_pattern.search(content):
            all_findings.append(
                Finding(
                    priority="P1",
                    category="ATS / Info.plist",
                    path=str(plist_path.relative_to(root)),
                    line_no=0,
                    line="(file contains NSAllowsArbitraryLoads)",
                    note="Review App Transport Security settings in Info.plist.",
                )
            )

    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    all_findings.sort(
        key=lambda f: (priority_order.get(f.priority, 9), f.path, f.line_no)
    )

    lines = [
        "# Security pattern scan (heuristic)",
        "",
        "_This is static pattern matching, not a full SAST or dependency audit. Triaged items need human review._",
        "",
        f"Swift files scanned: **{len(swift_files)}**",
        f"Plist files scanned for ATS: **{len(plist_files)}**",
        f"Findings: **{len(all_findings)}**",
        "",
        "| Priority | Meaning |",
        "|----------|---------|",
        "| **P1** | Address before release — ATS bypass, suspected secrets |",
        "| **P2** | Review soon — logging, HTTP, validation |",
        "| **P3** | Hardening — force unwraps in sensitive paths |",
        "",
    ]

    if not all_findings:
        lines.append("_No heuristic security patterns matched._")
    else:
        lines.extend(
            [
                "| Priority | Category | Location | Snippet | Guidance |",
                "|------------|----------|----------|---------|----------|",
            ]
        )
        for f in all_findings:
            loc = f.path if f.line_no == 0 else f"{f.path}:{f.line_no}"
            snippet = f.line.replace("|", "\\|")
            note = f.note.replace("|", "\\|")
            lines.append(
                f"| {f.priority} | {f.category} | `{loc}` | {snippet} | {note} |"
            )

    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

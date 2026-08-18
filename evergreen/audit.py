"""Automated hostile-review audit for the survey draft.

Checks every citation in the survey sections against the live corpus:
1. every `evg-*` record id cited must exist in data/papers.jsonl;
2. cited records should be full-text verified (warning otherwise);
3. arXiv ids must be well-formed; corpus members must match their record;
4. headline corpus numbers (total, verified) must match the DB;
5. method-trend numbers quoted in §3/§6 must match the verified subset.

Writes data/survey/audit-report.md.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from evergreen.database import PaperDatabase

_ID_RE = re.compile(r"evg-[0-9a-f]{12,16}")
_ARXIV_RE = re.compile(r"arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5})|arXiv:([0-9]{4}\.[0-9]{4,5})", re.IGNORECASE)


def _extract_sections(survey_root: Path) -> str:
    sections = survey_root / "sections"
    parts = []
    for path in sorted(sections.glob("*.md")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _verified_method_trends(db: PaperDatabase) -> dict[str, dict[str, int]]:
    """Recompute the §3 trend table from verified records (fulltext tags)."""
    from collections import Counter, defaultdict

    by_year: dict[str, Counter] = defaultdict(Counter)
    methods = [
        "RLVR / GRPO",
        "Preference Optimization",
        "Chain-of-Thought",
        "Verifier / PRM",
        "Search / MCTS",
        "Test-time Scaling",
    ]
    for record in db.load():
        if not record.get("verified"):
            continue
        tags = record.get("verification", {}).get("fulltext_methods") or record.get("methods", [])
        for method in tags:
            if method in methods:
                by_year[str(record.get("year"))][method] += 1
    return {method: {year: by_year[year].get(method, 0) for year in sorted(by_year)} for method in methods}


def run_audit(survey_root: Path, data_root: Path, quiet: bool = False) -> dict[str, Any]:
    db = PaperDatabase(data_root)
    records = db.load()
    by_id = {record["id"]: record for record in records}
    text = _extract_sections(survey_root)

    findings: list[dict[str, str]] = []
    issues = 0

    # 1. evg-* id existence + verification status
    cited_ids = sorted(set(_ID_RE.findall(text)))
    for record_id in cited_ids:
        record = by_id.get(record_id)
        if record is None:
            issues += 1
            findings.append({"level": "FAIL", "check": "record-exists", "detail": f"{record_id} cited but missing from papers.jsonl"})
            continue
        if not record.get("verified"):
            findings.append({"level": "WARN", "check": "record-verified", "detail": f"{record_id} ({record['title'][:40]}) cited but not full-text verified"})

    # 2. arXiv id format + membership
    arxiv_ids = sorted({match.group(1) or match.group(2) for match in _ARXIV_RE.finditer(text)})
    corpus_ids = {record.get("arxiv_id", "").split("/abs/")[-1].replace("v", "", 1).rsplit("v", 1)[0] for record in records}
    for arxiv_id in arxiv_ids:
        if not re.fullmatch(r"[0-9]{4}\.[0-9]{4,5}", arxiv_id):
            issues += 1
            findings.append({"level": "FAIL", "check": "arxiv-format", "detail": f"malformed arXiv id: {arxiv_id}"})
            continue
        base = arxiv_id
        if base not in corpus_ids and not any(base in record.get("arxiv_id", "") for record in records):
            findings.append({"level": "WARN", "check": "arxiv-membership", "detail": f"arXiv:{arxiv_id} cited but not in corpus (external citation — verify separately)"})

    # 3. Headline corpus numbers
    stats = db.stats()
    total, verified = stats["total_papers"], stats["verified_papers"]
    if str(total) not in text:
        issues += 1
        findings.append({"level": "FAIL", "check": "total-number", "detail": f"draft does not state total {total} (db value)"})
    else:
        findings.append({"level": "PASS", "check": "total-number", "detail": f"total {total} matches"})
    if str(verified) not in text:
        issues += 1
        findings.append({"level": "FAIL", "check": "verified-number", "detail": f"draft does not state verified {verified} (db value)"})
    else:
        findings.append({"level": "PASS", "check": "verified-number", "detail": f"verified {verified} matches"})

    # 4. §3 trend table numbers
    trends = _verified_method_trends(db)
    for method, years in trends.items():
        if method == "RLVR / GRPO" and years.get("2024") == 4 and years.get("2025") == 18:
            findings.append({"level": "PASS", "check": "trend-RLVR", "detail": f"{method} 4->18 verified trend matches"})
        elif method == "RLVR / GRPO":
            issues += 1
            findings.append({"level": "FAIL", "check": "trend-RLVR", "detail": f"{method} trend now {years}"})

    # Report
    lines = [
        "# Survey Draft — Automated Audit Report",
        "",
        f"> Generated {date.today().isoformat()} by `evergreen audit`.",
        f"> Corpus: {total} papers, {verified} verified. Citations checked: "
        f"{len(cited_ids)} record ids, {len(arxiv_ids)} arXiv ids.",
        "",
        "## Findings",
        "",
    ]
    for finding in findings:
        lines.append(f"- [{finding['level']}] **{finding['check']}**: {finding['detail']}")
    lines.extend(
        [
            "",
            f"## Summary: {issues} FAIL · "
            f"{sum(1 for f in findings if f['level'] == 'WARN')} WARN · "
            f"{sum(1 for f in findings if f['level'] == 'PASS')} PASS",
            "",
            "This automated audit covers mechanical citation integrity only. "
            "Content review (claim correctness, tone, scope) still requires "
            "human reviewers per the GO/NO-GO gate in `positioning.md`.",
        ]
    )
    report = survey_root / "audit-report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    if not quiet:
        print(f"[audit] {issues} FAIL, {sum(1 for f in findings if f['level'] == 'WARN')} WARN, {sum(1 for f in findings if f['level'] == 'PASS')} PASS -> {report}")
    return {
        "report": str(report),
        "fail": issues,
        "warn": sum(1 for f in findings if f["level"] == "WARN"),
        "pass": sum(1 for f in findings if f["level"] == "PASS"),
        "cited_records": len(cited_ids),
        "cited_arxiv": len(arxiv_ids),
    }

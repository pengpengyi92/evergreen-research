"""Research-group tracking & distillation (AI/Quant scope).

Pulls recent works per watched institution from OpenAlex, reconstructs
abstracts, classifies into AI/Quant relevance with the deterministic
taggers, and aggregates per-group reports: papers, top authors, method
mix, year distribution, citation headroom.

Watchlist (default): HK universities.
    data/groups.json          — machine-readable aggregate
    data/groups/<slug>.md     — per-group distillation report
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from evergreen.structurer import detect_benchmarks, detect_methods

GROUP_WATCHLIST: dict[str, dict[str, object]] = {
    "hku-cs": {
        "name": "HKU Computer Science (CS / CDS)",
        "search": "computer science university of hong kong",
        "per_page": 40,
        "require": "university of hong kong",
        "exclude": "science and technology",
        "require_raw": ["computer science", "computing and data science"],
    },
    "hku-ds": {
        "name": "HKU Data Science / Statistics",
        "search": "data science university of hong kong",
        "per_page": 40,
        "require": "university of hong kong",
        "exclude": "science and technology",
        "require_raw": [
            "data science",
            "statistics and actuarial science",
            "institute of data science",
        ],
    },
    "hku": {
        "name": "The University of Hong Kong (HKU)",
        "search": '"University of Hong Kong"',
        "require": "university of hong kong",
        "exclude": "science and technology",
    },
    "hkust-gz": {
        "name": "HKUST (Guangzhou)",
        "search": '"Hong Kong University of Science and Technology"',
        "require": "guangzhou",
    },
    "hkust": {
        "name": "Hong Kong University of Science and Technology (HKUST)",
        "search": '"Hong Kong University of Science and Technology"',
        "require": "hong kong university of science and technology",
        "exclude": "guangzhou",
    },
    "cuhk-shenzhen": {
        "name": "The Chinese University of Hong Kong, Shenzhen (CUHK-SZ)",
        "search": '"Chinese University of Hong Kong, Shenzhen"',
        "require": "shenzhen",
    },
    "cuhk": {
        "name": "The Chinese University of Hong Kong (CUHK)",
        "search": '"Chinese University of Hong Kong"',
        "require": "chinese university of hong kong",
        "exclude": "shenzhen",
    },
}

_AI_QUANT_KEYWORDS = [
    "neural", "learning", "transformer", "language model", "llm", "agent",
    "reinforcement", "deep learning", "diffusion", "generation", "vision",
    "speech", "robotics", "optimization", "inference", "training", "reasoning",
    "trading", "portfolio", "stock", "market", "financial", "quantitative",
    "risk", "pricing", "forecast", "alpha", "factor",
]


def is_ai_quant(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _AI_QUANT_KEYWORDS)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def run_groups(
    data_root: Path,
    from_date: str = "2025-01-01",
    per_group: int = 40,
    quiet: bool = False,
) -> dict[str, Any]:
    from evergreen import openalex

    groups_dir = data_root / "groups"
    groups_dir.mkdir(parents=True, exist_ok=True)
    existing_path = data_root / "groups.json"
    existing: dict[str, Any] = {}
    if existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8")).get("groups", {})
        except (OSError, ValueError):
            existing = {}
    aggregate: dict[str, Any] = {
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "groups": dict(existing),
    }
    consecutive_failures = 0

    for slug, spec in GROUP_WATCHLIST.items():
        group_per_page = int(spec.get("per_page", per_group))
        try:
            works = openalex.works_by_institution(spec["search"], from_date=from_date, per_page=group_per_page)
        except Exception as exc:
            consecutive_failures += 1
            if not quiet:
                print(f"[groups] {slug}: {exc}")
            if consecutive_failures >= 2:
                print("[groups] circuit breaker: OpenAlex rate limit, stopping remaining groups")
                break
            continue
        consecutive_failures = 0
        require = str(spec.get("require", "")).lower()
        exclude = str(spec.get("exclude", "")).lower()
        require_raw = [term.lower() for term in spec.get("require_raw", [])]
        works = [
            work
            for work in works
            if any(
                require in institution.lower()
                for institution in work.get("institutions", [])
            )
            and not (
                exclude
                and any(exclude in institution.lower() for institution in work.get("institutions", []))
            )
            and (
                not require_raw
                or any(
                    term in raw.lower()
                    for raw in work.get("affiliations_raw", [])
                    for term in require_raw
                )
            )
        ]
        papers: list[dict[str, Any]] = []
        for work in works:
            text = f"{work.get('title', '')} {work.get('abstract', '')}"
            if not is_ai_quant(text):
                continue
            papers.append(
                {
                    "title": work.get("title", ""),
                    "doi": work.get("doi"),
                    "openalex_id": work.get("openalex_id", ""),
                    "published": work.get("publication_date", ""),
                    "citations": work.get("cited_by_count"),
                    "methods": detect_methods(text),
                    "benchmarks": detect_benchmarks(text),
                }
            )
        methods = Counter(method for paper in papers for method in paper["methods"])
        authors = Counter(
            row["author"]
            for work in works
            for row in work.get("authorships", [])
            if row["author"]
        )
        years = Counter((paper.get("published") or "????")[:4] for paper in papers)
        aggregate["groups"][slug] = {
            "name": spec["name"],
            "papers": len(papers),
            "total_works_fetched": len(works),
            "top_methods": dict(methods.most_common(10)),
            "top_authors": dict(authors.most_common(10)),
            "years": dict(sorted(years.items())),
            "recent": papers[:12],
        }
        (data_root / "groups.json").write_text(
            json.dumps(aggregate, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        write_group_md(groups_dir, slug, spec, aggregate["groups"][slug])
        if not quiet:
            print(
                f"[groups] {slug}: {len(papers)} AI/quant papers "
                f"(from {len(works)} works)"
            )
    return aggregate


def write_group_md(
    groups_dir: Path,
    slug: str,
    spec: dict[str, str],
    group: dict[str, Any],
) -> Path:
    lines = [
        f"# {spec['name']} — Research Group Distillation",
        "",
        f"> Generated {time.strftime('%Y-%m-%d')} · scope: AI / Quant · "
        f"{group['papers']} papers classified from {group['total_works_fetched']} recent works.",
        "",
        "## Method mix",
        "",
    ]
    for method, count in group["top_methods"].items():
        lines.append(f"- {method}: {count}")
    lines.extend(
        [
            "",
            "## Top authors (affiliated, any field)",
            "",
        ]
    )
    for author, count in group["top_authors"].items():
        lines.append(f"- {author}: {count} works")
    lines.extend(
        [
            "",
            "## Publication years (AI/quant)",
            "",
            f"- {group['years']}",
            "",
            "## Recent AI/Quant papers",
            "",
        ]
    )
    for paper in group["recent"]:
        methods = ", ".join(paper["methods"][:4]) or "—"
        lines.append(
            f"- **{paper['title']}** ({paper['published'][:7]}, "
            f"cited {paper['citations']}) — {methods}"
        )
    lines.extend(
        [
            "",
            "---",
            "_Distilled from OpenAlex affiliation search; institutional "
            "attribution follows each work's authorship metadata._",
        ]
    )
    path = groups_dir / f"{slug}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

"""Method-overlap novelty scoring (corpus-side, no citation lag).

For papers too recent to have meaningful citation counts, novelty is
estimated from the *unusualness of the method vector* within its pillar
cohort: 1 - mean Jaccard similarity against same-pillar papers sharing at
least one method tag. Scores live in `data/novelty.jsonl` and blend with
citation data (§7.4) once both exist.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def method_vector(record: dict[str, Any]) -> frozenset[str]:
    return frozenset(record.get("methods", []))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def novelty_score(record: dict[str, Any], cohort: list[dict[str, Any]]) -> dict[str, Any]:
    """Score one record against its pillar cohort (excluding itself)."""
    vector = method_vector(record)
    similarities = [
        jaccard(vector, method_vector(other))
        for other in cohort
        if other.get("id") != record.get("id") and method_vector(other) & vector
    ]
    if not similarities:
        return {
            "id": record.get("id"),
            "novelty": 1.0,
            "cohort_overlap": 0,
            "basis": "no-method-overlap-in-cohort",
        }
    mean_overlap = sum(similarities) / len(similarities)
    return {
        "id": record.get("id"),
        "novelty": round(1.0 - mean_overlap, 4),
        "cohort_overlap": len(similarities),
        "mean_jaccard": round(mean_overlap, 4),
        "basis": "method-vector-overlap",
    }


def blend_scores(
    data_root: Path,
    pillar: str,
    quiet: bool = False,
) -> dict[str, Any]:
    """Blend method-overlap novelty with citation data where available (§7.4).

    blend = 0.5 * novelty + 0.5 * citation_component; the citation component
    is the log-scaled citation count when S2 data exists, otherwise the
    method-novelty stands alone (citation-lag immune).
    """
    import math

    from evergreen.citations import CitationStore

    store = CitationStore(data_root)
    citations = store.load()
    novelty_path = data_root / "novelty.jsonl"
    if not novelty_path.exists():
        return {"error": "run `evergreen novelty` first"}
    rows = [
        json.loads(line)
        for line in novelty_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = [row for row in rows if row.get("pillar") == pillar]
    # keep the newest score per record id
    newest: dict[str, dict[str, Any]] = {}
    for row in rows:
        newest[row["id"]] = row
    blended: list[dict[str, Any]] = []
    for record_id, row in newest.items():
        citation = citations.get(f"arXiv:{row.get('arxiv_id', '')}") or citations.get(record_id)
        if citation and citation.get("citationCount") is not None:
            log_component = math.log1p(citation["citationCount"]) / math.log1p(10000)
            blend = round(0.5 * row["novelty"] + 0.5 * log_component, 4)
            basis = "novelty+citations"
        else:
            blend = row["novelty"]
            basis = "novelty-only"
        blended.append(
            {
                "id": record_id,
                "pillar": pillar,
                "novelty": row["novelty"],
                "citations": citation.get("citationCount") if citation else None,
                "blend": blend,
                "basis": basis,
                "computed_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
    blended.sort(key=lambda item: item["blend"], reverse=True)
    path = data_root / "novelty_blend.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for item in blended:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    if not quiet:
        print(f"[blend] {len(blended)} records -> {path}")
        for item in blended[:5]:
            print(f"  {item['blend']:.3f}  {item['id'][:16]}  ({item['basis']}, cit {item['citations']})")
    return {
        "store": str(path),
        "scored": len(blended),
        "with_citations": sum(1 for item in blended if item["basis"] == "novelty+citations"),
        "top": [{"id": item["id"], "blend": item["blend"]} for item in blended[:10]],
    }


def run_novelty(
    data_root: Path,
    pillar: str,
    verified_only: bool = True,
    quiet: bool = False,
) -> dict[str, Any]:
    """Score all records of a pillar; persist to data/novelty.jsonl."""
    from evergreen.database import PaperDatabase

    db = PaperDatabase(data_root)
    records = [record for record in db.load() if record.get("pillar") == pillar]
    if verified_only:
        records = [record for record in records if record.get("verified")]
    scored = [novelty_score(record, records) for record in records]
    scored.sort(key=lambda item: item["novelty"], reverse=True)

    store = data_root / "novelty.jsonl"
    computed_on = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data_root.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as handle:
        for item in scored:
            handle.write(json.dumps({"computed_on": computed_on, "pillar": pillar, **item}, ensure_ascii=False) + "\n")

    if not quiet:
        print(f"[novelty] scored {len(scored)} {pillar} records -> {store}")
        for item in scored[:5]:
            print(f"  {item['novelty']:.3f}  {item['id'][:16]}  (overlap {item['cohort_overlap']})")
    return {
        "pillar": pillar,
        "scored": len(scored),
        "store": str(store),
        "top": [
            {"id": item["id"], "novelty": item["novelty"]}
            for item in scored[:10]
        ],
    }

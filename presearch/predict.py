"""Research-market prediction v0: top-venue acceptance odds.

Quant lens on papers: features -> a deterministic "top-venue odds" score.

    odds = 0.35 * log-citations + 0.25 * novelty + 0.30 * venue-topic
           overlap + 0.10 * verified bonus

This is a heuristic, not peer review: it ranks which corpus papers are
most likely to land at ICML/ICLR/NeurIPS, so the weekly sweep doubles as
a "top-venue radar". Labels for a supervised v1 come from OpenAlex venue
metadata (citations.jsonl already carries venue per record).
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from presearch.database import PaperDatabase
from presearch.citations import CitationStore

VENUE_TOPICS: dict[str, list[str]] = {
    "ICML": [
        "optimization", "generalization", "convergence", "theory",
        "probabilistic", "kernel", "bayesian", "implicit bias",
        "sharpness", "convex", "regret", "sample complexity",
    ],
    "ICLR": [
        "representation", "transformer", "llm", "scaling", "pretraining",
        "fine-tuning", "in-context", "benchmark", "reasoning", "routing",
        "mixture-of-experts", "world model", "diffusion",
    ],
    "NeurIPS": [
        "benchmark", "dataset", "robust", "fairness", "generative",
        "multimodal", "agent", "safety", "alignment", "interpretability",
        "reinforcement", "continual", "federated",
    ],
}

TOP_VENUE_NAMES = {
    "international conference on machine learning": "ICML",
    "international conference on learning representations": "ICLR",
    "neural information processing systems": "NeurIPS",
    "neurips": "NeurIPS",
    "icml": "ICML",
    "iclr": "ICLR",
}


def _log_citation(citation_count) -> float:
    if citation_count is None:
        return 0.0
    return math.log1p(citation_count) / math.log1p(10000)


def _topic_overlap(text: str) -> float:
    lowered = text.lower()
    hits = sum(1 for topics in VENUE_TOPICS.values() for t in topics if t in lowered)
    total = sum(len(topics) for topics in VENUE_TOPICS.values())
    return min(1.0, hits / max(total * 0.12, 1))


def run_predict(
    data_root: Path,
    top_n: int = 20,
    quiet: bool = False,
) -> dict[str, Any]:
    db = PaperDatabase(data_root)
    records = db.load()
    citations = CitationStore(data_root).load()

    novelty_by_id: dict[str, float] = {}
    blend_path = data_root / "novelty_blend.jsonl"
    if blend_path.exists():
        for line in blend_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            novelty_by_id[row.get("id", "")] = row.get("novelty", 0.5)

    scored: list[dict[str, Any]] = []
    for record in records:
        base_arxiv = (record.get("arxiv_id") or "").split("/abs/")[-1]
        citation = citations.get(f"arXiv:{base_arxiv}")
        citation_count = citation.get("citationCount") if citation else None
        text = f"{record.get('title', '')} {record.get('abstract', '')}"
        odds = round(
            0.35 * _log_citation(citation_count)
            + 0.25 * novelty_by_id.get(record.get("id", ""), 0.5)
            + 0.30 * _topic_overlap(text)
            + 0.10 * (1.0 if record.get("verified") else 0.0),
            4,
        )
        scored.append(
            {
                "id": record.get("id", ""),
                "title": record.get("title", ""),
                "arxiv_id": record.get("arxiv_id", ""),
                "pillar": record.get("pillar", ""),
                "odds": odds,
                "citations": citation_count,
                "verified": bool(record.get("verified")),
                "year": record.get("year", ""),
            }
        )
    scored.sort(key=lambda row: (-row["odds"], -(row["citations"] or 0)))
    top = scored[:top_n]

    path = data_root / "venue-odds.json"
    payload = {
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": "deterministic-heuristic-v0 (0.35 log-citations + 0.25 novelty + 0.30 topic-overlap + 0.10 verified)",
        "top": top,
        "all": scored,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Top-Venue Radar — Research-Market Prediction v0",
        "",
        f"> Generated {time.strftime('%Y-%m-%d')} · deterministic heuristic, "
        "not peer review. Ranks corpus papers by predicted ICML/ICLR/NeurIPS "
        "acceptance odds.",
        "",
        "| rank | paper | pillar | odds | citations | verified |",
        "|------|-------|--------|------|-----------|----------|",
    ]
    for index, row in enumerate(top, start=1):
        arxiv_short = row["arxiv_id"].split("/abs/")[-1]
        lines.append(
            f"| {index} | {row['title'][:60]} ([{arxiv_short}]({row['arxiv_id']})) "
            f"| {row['pillar']} | {row['odds']:.3f} | {row['citations']} | "
            f"{'✓' if row['verified'] else ''} |"
        )
    lines.extend(
        [
            "",
            "---",
            "_Supervised v1 (OpenAlex venue labels -> logistic model) is the "
            "roadmap next step; this heuristic is the calibrated-tomorrow, "
            "rankable-today version._",
        ]
    )
    md_path = data_root / "venue-odds.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    if not quiet:
        print(f"[predict] scored {len(scored)} papers -> {path}")
        for row in top[:5]:
            print(f"  {row['odds']:.3f}  {row['title'][:60]}")
    return {"store": str(path), "report": str(md_path), "scored": len(scored),
            "top": [{"title": r["title"], "odds": r["odds"]} for r in top[:10]]}

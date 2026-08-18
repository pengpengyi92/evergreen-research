"""High-dimensional paper matrix: TF-IDF vectors, cosine search, k-means.

Treats the corpus like quant-style high-dimensional data: every paper is a
vector over a shared term space; queries, similarities, and clusters are
batch-computable and cheap. stdlib-only.

Artifacts:
    data/matrix.json    — term vocabulary, idf, per-paper sparse vectors
    data/clusters.json  — k-means assignment + top terms per cluster
    data/clusters.md    — human-readable research-directions report
"""

from __future__ import annotations

import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "are", "was", "were", "from",
    "have", "has", "had", "not", "but", "all", "can", "may", "which", "their",
    "they", "them", "these", "those", "into", "over", "under", "than", "then",
    "its", "his", "her", "our", "your", "more", "most", "some", "such", "only",
    "also", "very", "been", "being", "will", "would", "could", "should", "about",
    "between", "through", "during", "before", "after", "above", "below", "out",
    "off", "each", "few", "both", "how", "why", "what", "when", "where", "who",
    "whom", "whose", "a", "an", "as", "at", "by", "in", "is", "it", "of", "on",
    "or", "to", "we", "be", "do", "if", "up", "so", "no", "he", "she", "me",
    "my", "us", "using", "use", "used", "based", "one", "two", "new", "via",
}

_TOKEN_RE = re.compile(r"[a-z][a-z0-9\-]{2,}")


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS and not token.isdigit()
    ]


def build_matrix(records: list[dict[str, Any]], max_features: int = 4000) -> dict[str, Any]:
    """Compute TF-IDF vectors for every record (title + abstract)."""
    doc_tokens: list[Counter] = []
    for record in records:
        text = f"{record.get('title', '')} {record.get('abstract', '')}"
        doc_tokens.append(Counter(tokenize(text)))
    document_frequency: Counter = Counter()
    for counter in doc_tokens:
        document_frequency.update(counter.keys())
    num_docs = max(len(records), 1)
    # keep the most discriminative terms: medium df (not hapax, not ubiquitous)
    candidates = [
        (term, count) for term, count in document_frequency.items() if 1 < count < num_docs * 0.9
    ]
    candidates.sort(key=lambda item: -item[1])
    vocabulary = [term for term, _ in candidates[:max_features]]
    idf = {
        term: math.log((1 + num_docs) / (1 + document_frequency[term])) + 1.0
        for term in vocabulary
    }
    vectors: list[dict[str, float]] = []
    for counter in doc_tokens:
        total = sum(counter.values()) or 1
        vector = {}
        for term in vocabulary:
            if counter[term]:
                vector[term] = (counter[term] / total) * idf[term]
        vectors.append(vector)
    return {"vocabulary": vocabulary, "idf": idf, "vectors": vectors}


def _norm(vector: dict[str, float]) -> float:
    return math.sqrt(sum(value * value for value in vector.values())) or 1.0


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(value * b.get(term, 0.0) for term, value in a.items())
    return dot / (_norm(a) * _norm(b))


def query(matrix: dict[str, Any], records: list[dict[str, Any]], text: str, k: int = 10) -> list[dict[str, Any]]:
    """Top-k cosine nearest papers for a free-text query."""
    query_counter = Counter(tokenize(text))
    total = sum(query_counter.values()) or 1
    query_vector = {
        term: (query_counter[term] / total) * matrix["idf"].get(term, 1.0)
        for term in query_counter
        if term in matrix["idf"]
    }
    scored = [
        (cosine(query_vector, vector), index)
        for index, vector in enumerate(matrix["vectors"])
    ]
    scored.sort(key=lambda item: -item[0])
    results = []
    for score, index in scored[:k]:
        record = records[index]
        results.append(
            {
                "score": round(score, 4),
                "id": record.get("id", ""),
                "title": record.get("title", ""),
                "pillar": record.get("pillar", ""),
                "year": record.get("year", ""),
                "arxiv_id": record.get("arxiv_id", ""),
            }
        )
    return results


def kmeans(matrix: dict[str, Any], k: int = 10, max_iter: int = 25) -> list[int]:
    """Simple spherical-style k-means over the sparse vectors."""
    vectors = matrix["vectors"]
    vocabulary = matrix["vocabulary"]
    num_docs = len(vectors)
    if num_docs <= k:
        return list(range(num_docs)) + [0] * (k - num_docs)
    # initialize centers from spread-out documents
    centers: list[dict[str, float]] = []
    step = max(1, num_docs // k)
    for index in range(0, num_docs, step):
        centers.append(dict(vectors[index]))
        if len(centers) == k:
            break
    assignment = [0] * num_docs
    for _ in range(max_iter):
        changed = 0
        for index, vector in enumerate(vectors):
            best_cluster = max(
                range(k),
                key=lambda cluster: cosine(vector, centers[cluster]),
            )
            if assignment[index] != best_cluster:
                assignment[index] = best_cluster
                changed += 1
        if changed == 0:
            break
        # recompute centers as mean of members (re-normalized)
        sums: list[Counter] = [Counter() for _ in range(k)]
        counts = [0] * k
        for index, cluster in enumerate(assignment):
            sums[cluster].update(vectors[index])
            counts[cluster] += 1
        for cluster in range(k):
            if counts[cluster]:
                norm = math.sqrt(sum(v * v for v in sums[cluster].values())) or 1.0
                centers[cluster] = {
                    term: value / norm for term, value in sums[cluster].items()
                }
    return assignment


def cluster_report(
    matrix: dict[str, Any],
    records: list[dict[str, Any]],
    assignment: list[int],
    k: int,
    top_terms: int = 8,
) -> dict[str, Any]:
    """Summarize each cluster: top terms + top papers + pillar mix."""
    clusters: list[dict[str, Any]] = []
    for cluster_id in range(k):
        members = [
            index for index, assigned in enumerate(assignment) if assigned == cluster_id
        ]
        if not members:
            clusters.append({"cluster": cluster_id, "size": 0})
            continue
        term_scores: Counter = Counter()
        for index in members:
            term_scores.update(matrix["vectors"][index])
        pillars = Counter(records[index].get("pillar", "?") for index in members)
        years = Counter(str(records[index].get("year", "?")) for index in members)
        papers = sorted(
            members,
            key=lambda index: -sum(matrix["vectors"][index].values()),
        )[:5]
        clusters.append(
            {
                "cluster": cluster_id,
                "size": len(members),
                "top_terms": [term for term, _ in term_scores.most_common(top_terms)],
                "pillars": dict(pillars.most_common()),
                "years": dict(sorted(years.items())),
                "top_papers": [
                    {
                        "title": records[index].get("title", "")[:80],
                        "id": records[index].get("id", ""),
                        "arxiv_id": records[index].get("arxiv_id", ""),
                    }
                    for index in papers
                ],
            }
        )
    return {"k": k, "clusters": clusters}


def save_matrix(data_root: Path, matrix: dict[str, Any]) -> Path:
    path = data_root / "matrix.json"
    path.write_text(json.dumps(matrix, ensure_ascii=False), encoding="utf-8")
    return path


def load_matrix(data_root: Path) -> dict[str, Any]:
    return json.loads((data_root / "matrix.json").read_text(encoding="utf-8"))


def write_clusters_md(data_root: Path, report: dict[str, Any]) -> Path:
    lines = [
        "# Research Directions — Automatic Cluster Report",
        "",
        f"> Generated {time.strftime('%Y-%m-%d')} from the TF-IDF matrix over the corpus. "
        f"k = {report['k']}. Clusters are data-driven, not hand-labeled.",
        "",
    ]
    for cluster in report["clusters"]:
        if not cluster.get("size"):
            continue
        lines.append(
            f"## Cluster {cluster['cluster']}: "
            f"{', '.join(cluster['top_terms'][:6])} ({cluster['size']} papers)"
        )
        lines.append("")
        lines.append(f"- pillars: {cluster['pillars']} · years: {cluster['years']}")
        for paper in cluster["top_papers"]:
            lines.append(f"- {paper['title']} ({paper['arxiv_id'].split('/abs/')[-1]})")
        lines.append("")
    path = data_root / "clusters.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

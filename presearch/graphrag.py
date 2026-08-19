"""GraphRAG-lite: relation graph + communities over the paper corpus.

Why this works so well here: classic GraphRAG's hardest step — entity
extraction — is already done deterministically by the corpus pipeline
(methods/benchmarks/pillars are the entities; papers are the documents).
So we build the graph directly:

    nodes: paper / method / benchmark / pillar
    edges: paper-USES-method, paper-EVALUATED_ON-benchmark,
           paper-IN-pillar, method-CO_OCCURS-method (>=2 shared papers)

Then: deterministic label-propagation communities, community summaries,
and a map-reduce query (per-community local score -> top communities).
Zero dependencies, reproducible, same philosophy as everything else.
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

MAX_BENCHMARKS_PER_PAPER = 6
CO_OCCUR_MIN = 2
LABEL_PROP_ITERS = 12


def build_graph(papers: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    def add_node(node_id: str, node_type: str, label: str, meta: dict[str, Any] | None = None) -> None:
        nodes.setdefault(node_id, {"id": node_id, "type": node_type, "label": label, "meta": meta or {}})

    method_pairs: Counter = Counter()
    for paper in papers:
        paper_id = paper.get("id", "")
        if not paper_id:
            continue
        add_node(paper_id, "paper", paper.get("title", "")[:80],
                 {"pillar": paper.get("pillar", ""), "year": paper.get("year", ""),
                  "verified": bool(paper.get("verified")), "arxiv_id": paper.get("arxiv_id", "")})
        methods = paper.get("methods", [])[:8]
        for method in methods:
            add_node(f"method:{method}", "method", method)
            edges.append({"src": paper_id, "dst": f"method:{method}", "rel": "USES"})
        for benchmark in paper.get("benchmarks", [])[:MAX_BENCHMARKS_PER_PAPER]:
            add_node(f"benchmark:{benchmark}", "benchmark", benchmark)
            edges.append({"src": paper_id, "dst": f"benchmark:{benchmark}", "rel": "EVALUATED_ON"})
        pillar = paper.get("pillar", "")
        if pillar:
            add_node(f"pillar:{pillar}", "pillar", pillar)
            edges.append({"src": paper_id, "dst": f"pillar:{pillar}", "rel": "IN_PILLAR"})
        for i, method_a in enumerate(methods):
            for method_b in methods[i + 1:]:
                method_pairs[(f"method:{method_a}", f"method:{method_b}")] += 1

    for (a, b), count in method_pairs.items():
        if count >= CO_OCCUR_MIN:
            edges.append({"src": a, "dst": b, "rel": "CO_OCCURS", "weight": count})
    return nodes, edges


def label_propagation(nodes: dict[str, dict[str, Any]], edges: list[dict[str, str]]) -> dict[str, int]:
    node_ids = sorted(nodes.keys())
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["src"]].append(edge["dst"])
        adjacency[edge["dst"]].append(edge["src"])
    labels = {node_id: index for index, node_id in enumerate(node_ids)}
    for _ in range(LABEL_PROP_ITERS):
        changed = 0
        for node_id in node_ids:
            neighbors = adjacency.get(node_id, [])
            if not neighbors:
                continue
            votes = Counter(labels[n] for n in neighbors)
            best = max(votes, key=lambda k: (votes[k], -k))
            if labels[node_id] != best:
                labels[node_id] = best
                changed += 1
        if changed == 0:
            break
    # 重映射为连续社区号（保持确定性顺序）
    remap: dict[int, int] = {}
    communities: dict[str, int] = {}
    for node_id in node_ids:
        label = labels[node_id]
        if label not in remap:
            remap[label] = len(remap)
        communities[node_id] = remap[label]
    return communities


def summarize_communities(
    nodes: dict[str, dict[str, Any]],
    communities: dict[str, int],
    edges: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_community: dict[int, list[str]] = defaultdict(list)
    for node_id, community in communities.items():
        by_community[community].append(node_id)

    summaries: list[dict[str, Any]] = []
    for community in sorted(by_community):
        members = by_community[community]
        types = Counter(nodes[n]["type"] for n in members)
        method_labels = [nodes[n]["label"] for n in members if nodes[n]["type"] == "method"]
        pillar_labels = [nodes[n]["label"] for n in members if nodes[n]["type"] == "pillar"]
        papers = [n for n in members if nodes[n]["type"] == "paper"]
        years = Counter(str(nodes[n]["meta"].get("year", "?")) for n in papers)
        verified = sum(1 for n in papers if nodes[n]["meta"].get("verified"))
        # 代表论文：核验优先，其次标题长度稳定排序（确定性）
        papers_sorted = sorted(
            papers,
            key=lambda n: (not nodes[n]["meta"].get("verified"), nodes[n]["label"]),
        )
        summaries.append(
            {
                "community": community,
                "size": len(members),
                "type_mix": dict(types.most_common()),
                "methods": method_labels,
                "pillars": pillar_labels,
                "papers": len(papers),
                "verified": verified,
                "years": dict(sorted(years.items())),
                "representatives": [
                    {"title": nodes[n]["label"], "arxiv_id": nodes[n]["meta"].get("arxiv_id", "")}
                    for n in papers_sorted[:3]
                ],
            }
        )
    summaries.sort(key=lambda s: -s["size"])
    return summaries


def query_communities(
    query_text: str,
    nodes: dict[str, dict[str, Any]],
    communities: dict[str, int],
    summaries: list[dict[str, Any]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    tokens = {t for t in query_text.lower().split() if len(t) > 2}
    if not tokens:
        return []
    by_community: dict[int, list[str]] = defaultdict(list)
    for node_id, community in communities.items():
        by_community[community].append(node_id)

    scored: list[dict[str, Any]] = []
    for summary in summaries:
        members = by_community[summary["community"]]
        label_text = " ".join(nodes[n]["label"].lower() for n in members)
        hits = sum(1 for t in tokens if t in label_text)
        member_hits = sum(
            1 for t in tokens
            for n in members
            if t in nodes[n]["label"].lower()
        )
        local_score = hits * 1.0 + member_hits * 0.5
        if local_score > 0:
            scored.append({**summary, "query_score": round(local_score, 2)})
    scored.sort(key=lambda s: -s["query_score"])
    return scored[:top_k]


def build_graphrag(data_root: Path) -> dict[str, Any]:
    papers_path = data_root / "papers.jsonl"
    papers = [
        json.loads(line)
        for line in papers_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    nodes, edges = build_graph(papers)
    communities = label_propagation(nodes, edges)
    summaries = summarize_communities(nodes, communities, edges)
    payload = {
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nodes": nodes,
        "edges": edges,
        "communities": {node_id: int(c) for node_id, c in communities.items()},
        "summaries": summaries,
    }
    out_dir = data_root / "graphrag"
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_path = out_dir / "graph.json"
    graph_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# GraphRAG 社区报告 — 研究市场的关系图谱",
        "",
        f"> 生成于 {time.strftime('%Y-%m-%d')} · 节点 {len(nodes)} · 边 {len(edges)} · "
        f"社区 {len(summaries)} 个 · 标签传播（确定性）",
        "",
    ]
    for index, summary in enumerate(summaries, start=1):
        lines.append(f"## 社区 {index}（{summary['size']} 节点 · {summary['papers']} 论文 · "
                     f"{summary['verified']} 核验）")
        lines.append("")
        lines.append(f"- 构成：{summary['type_mix']}")
        lines.append(f"- 方法族：{', '.join(summary['methods'][:8]) or '—'}")
        lines.append(f"- 支柱：{', '.join(summary['pillars']) or '—'} · 年份：{summary['years']}")
        for rep in summary["representatives"]:
            arxiv_short = rep["arxiv_id"].split("/abs/")[-1]
            lines.append(f"- {rep['title'][:70]} ({arxiv_short})")
        lines.append("")
    md_path = out_dir / "communities.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "graph": str(graph_path),
        "report": str(md_path),
        "nodes": len(nodes),
        "edges": len(edges),
        "communities": len(summaries),
        "top_communities": [
            {"size": s["size"], "methods": s["methods"][:5], "pillars": s["pillars"]}
            for s in summaries[:6]
        ],
    }

"""Deterministic arXiv-entry -> structured paper record.

Keyword tables and regexes extract methods, benchmarks, models, and result
sentences. No LLM calls: every tag is auditable against the abstract.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

METHOD_KEYWORDS: dict[str, list[str]] = {
    "RLVR / GRPO": ["rlvr", "grpo", "group relative policy", "reinforcement learning", "reward model", "policy optimization", "verifiable reward"],
    "Search / MCTS": ["mcts", "monte carlo tree", "tree search", "beam search", "best-of-n", "lookahead"],
    "Verifier / PRM": ["verifier", "process reward", "outcome reward", "prm", "orm", "reward modeling"],
    "Chain-of-Thought": ["chain-of-thought", "chain of thought", "reasoning trace", "think step", "cot"],
    "Test-time Scaling": ["test-time", "inference-time", "compute-optimal", "scaling inference", "overthinking"],
    "MoE": ["mixture-of-experts", "moe", "expert routing", "sparse expert", "top-k routing"],
    "Distillation": ["distill", "knowledge transfer"],
    "Quantization": ["quantiz", "int4", "int8", "fp8", "low-bit", "weight compression"],
    "KV Cache": ["kv cache", "kv-cache", "attention cache", "token cache"],
    "Long Context": ["long-context", "long context", "context window", "extended context", "context length"],
    "Speculative Decoding": ["speculative decoding", "speculative"],
    "Preference Optimization": ["dpo", "ppo", "preference optimization", "rlhf", "alignment", "sft"],
    "Interpretability": ["interpretab", "mechanistic", "circuit", "feature attribution", "probing"],
    "Safety / Jailbreak": ["jailbreak", "red-team", "red team", "safety", "harmful", "adversarial attack", "refusal"],
    "Multi-Agent": ["multi-agent", "multiagent", "agent collaboration", "agent society", "swarm", "agentic"],
    "Tool Use": ["tool use", "tool-use", "function calling", "api call", "tool learning"],
    "Memory / RAG": ["memory", "retrieval-augmented", "rag", "context management", "vector store"],
    "Computer Use": ["computer use", "gui agent", "desktop agent", "browser agent", "screen"],
    "Deep Research": ["deep research", "deep-research", "research agent", "autonomous research", "literature"],
    "World Model": ["world model", "world-model"],
    "Video Generation": ["video generation", "text-to-video", "diffusion"],
    "VLM": ["vision-language", "vlm", "multimodal", "image-text"],
    "Quant / Trading": ["trading", "stock", "portfolio", "financial", "factor model", "forecast", "alpha", "market prediction", "stock market", "financial market", "order book"],
}

BENCHMARKS = [
    "MMLU", "MMLU-Pro", "GSM8K", "MATH", "AIME", "GPQA", "HumanEval", "MBPP",
    "SWE-bench", "LiveCodeBench", "ARC-AGI", "HellaSwag", "TruthfulQA", "BBH",
    "IFEval", "MMMU", "Video-MME", "VQAv2", "ImageNet", "COCO",
    "AlpacaEval", "MT-Bench", "Chatbot Arena", "GAIA", "WebArena", "OSWorld",
    "AgentBench", "τ-bench", "BIG-Bench", "BigBench-Hard", "SimpleQA",
    "DROP", "HotpotQA", "SQuAD", "LAMBADA", "WikiText",
    "Q-Bench", "DocVQA", "OCRBench", "ChartQA", "FinQA", "TAT-QA",
]

MODEL_PATTERNS = [
    r"GPT-4[\w.-]*", r"GPT-3[\w.-]*", r"GPT-5[\w.-]*", r"o1[\w.-]*", r"o3[\w.-]*",
    r"Claude[\w .-]*", r"Gemini[\w .-]*", r"Llama[ -]?[\d\w.-]*", r"LLaMA[ -]?[\d\w.-]*",
    r"Qwen[\w.-]*", r"DeepSeek[\w.-]*", r"R1[\w.-]*", r"V3[\w.-]*",
    r"Mistral[\w .-]*", r"Mixtral[\w .-]*", r"Phi-?[\d\w.-]*", r"InternVL[\w.-]*",
    r"LLaVA[\w.-]*", r"Grok[\w .-]*", r"Falcon[\w .-]*", r"GLM-?[\d\w.-]*",
    r"Baichuan[\w.-]*", r"Yi-?[\d\w.-]*", r"Gemma[\w .-]*", r"PaLM[\w .-]*",
    r"BERT", r"T5", r"Stable Diffusion[\w .-]*", r"Flux[\w .-]*",
    r"Sora[\w .-]*", r"Kimi[\w .-]*", r"Kling[\w .-]*", r"Hunyuan[\w.-]*",
]

RESULT_MARKERS = [
    "state-of-the-art", "outperform", "achiev", "improves", "improve",
    "reduces", "surpass", "sota", "boost", "gains", "matches",
]

_SHORT_ACRONYMS = {
    "prm", "orm", "cot", "dpo", "ppo", "sft", "moe", "vlm", "rag", "rlhf",
    "mcts", "rlvr", "grpo", "sota", "lora",
}


def _keyword_hits(text: str, keyword: str) -> bool:
    if keyword in _SHORT_ACRONYMS:
        return bool(re.search(rf"\b{re.escape(keyword)}\b", text))
    return keyword in text


def detect_methods(text: str) -> list[str]:
    lowered = text.lower()
    return [
        method
        for method, keywords in METHOD_KEYWORDS.items()
        if any(_keyword_hits(lowered, keyword) for keyword in keywords)
    ]


def detect_benchmarks(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for benchmark in BENCHMARKS:
        name = benchmark.lower()
        if len(name) <= 5:
            hit = bool(re.search(rf"\b{re.escape(name)}\b", lowered))
        else:
            hit = name in lowered
        if hit and benchmark not in found:
            found.append(benchmark)
    return found


def detect_models(text: str) -> list[str]:
    found: list[str] = []
    for pattern in MODEL_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name = match.group(0).strip()
            if name and name not in found:
                found.append(name)
    return found


def _result_sentences(text: str, limit: int = 3) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    hits = [
        sentence.strip()
        for sentence in sentences
        if any(marker in sentence.lower() for marker in RESULT_MARKERS)
    ]
    return hits[:limit]


def _year(published: str) -> int:
    try:
        return int(published[:4])
    except (ValueError, TypeError):
        return datetime.now().year


def paper_id(entry: dict[str, Any]) -> str:
    arxiv_id = entry.get("arxiv_id") or entry.get("url") or entry.get("title") or "unknown"
    return "evg-" + hashlib.sha256(arxiv_id.encode("utf-8")).hexdigest()[:16]


def structure_entry(
    entry: dict[str, Any],
    pillar: str,
    swept_on: str,
    confidence: float = 0.6,
) -> dict[str, Any]:
    """Map one arXiv entry to an Evergreen paper record."""
    title = entry.get("title") or "untitled"
    abstract = entry.get("summary") or ""
    text = f"{title}. {abstract} " + " ".join(entry.get("categories", []))
    methods = detect_methods(text)
    benchmarks = detect_benchmarks(text)
    models = detect_models(text)
    results = _result_sentences(abstract) or (
        [re.split(r"(?<=[.!?])\s+", abstract.replace("\n", " "))[0]] if abstract else []
    )

    has_code_link = bool(
        re.search(r"github\.com|huggingface\.co|code is (available|released)", abstract, re.IGNORECASE)
        or (entry.get("comment") or "").lower().find("github") >= 0
    )
    score = confidence
    if len(abstract) > 200:
        score += 0.1
    if benchmarks:
        score += 0.1
    if has_code_link:
        score += 0.1
    score = round(min(score, 0.9), 2)

    return {
        "id": paper_id(entry),
        "title": title,
        "authors": entry.get("authors") or ["unknown"],
        "year": _year(entry.get("published", "")),
        "published": entry.get("published", ""),
        "updated": entry.get("updated", ""),
        "arxiv_id": entry.get("arxiv_id", ""),
        "url": entry.get("url") or f"https://arxiv.org/abs/{entry.get('arxiv_id', '')}",
        "primary_category": entry.get("primary_category") or "",
        "categories": entry.get("categories", []),
        "pillar": pillar,
        "methods": methods,
        "benchmarks": benchmarks,
        "models": models,
        "key_results": results,
        "abstract": abstract,
        "code_available": has_code_link,
        "confidence": score,
        "swept_on": swept_on,
    }

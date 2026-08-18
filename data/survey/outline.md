# Frontier AI — Living Survey Outline

> Working title: *The Compute-Allocation Frontier: A Living, Reproducible Survey of LLM Reasoning and Test-Time Compute*
> Status: evidence-accumulating (v0.4). 503 papers in corpus, 45 full-text verified.

## Section progress

- [x] §1 Introduction — drafted (`sections/01-introduction.md`)
- [x] §2 Method — drafted (`sections/02-method.md`)
- [x] §3 Foundations: CoT -> RLVR — drafted (`sections/03-foundations.md`)
- [ ] §4 Test-Time Compute
- [ ] §5 Cross-Pillar Convergence under a Compute-Allocation Lens
- [ ] §6 Empirical Trends from the Living Corpus
- [ ] §7 Open Problems, Risks, and Outlook
- [ ] Hostile review + citation audit

## Inclusion criteria (corpus v0.2)
- Published on arXiv 2023-01-01 or later, primary category in the six pillar scopes.
- Retrieved by the deterministic pillar queries; records are abstract-level until full-text verified.
- Records are append-only and deduplicated by arXiv id; retractions or withdrawn papers are excluded during weekly re-verification.
- A paper may enter the *core corpus* (citable claims) only after full-text verification (M2 gate).

## 1. Introduction
- [ ] The train-time -> test-time compute shift; why a living survey now.

## 2. Method: A Reproducible, Continuously-Updating Corpus Pipeline
- [ ] Six-pillar taxonomy, arXiv queries, deterministic structuring
- [ ] Append-only `data/papers.jsonl` and the evidence chain

## 3. Foundations: From Chain-of-Thought to RLVR
- [ ] Verifiable rewards, GRPO/PPO, reward hacking

## 4. Test-Time Compute
- [ ] Search (MCTS/beam), verifiers & PRMs
- [ ] Inference-time scaling laws and budget allocation

## 5. Cross-Pillar Convergence under a Compute-Allocation Lens

- [ ] LLM Reasoning / Test-time Compute — 77 papers
- [ ] Agentic AI / Deep Research Systems — 84 papers
- [ ] Efficient Training & Inference — 90 papers
- [ ] RL / Alignment / Safety — 75 papers
- [ ] Multimodal / World Models — 82 papers
- [ ] Quant × AI — 95 papers

## 6. Empirical Trends from the Living Corpus
- [ ] Method migration, benchmark saturation, convergence clusters

## 7. Open Problems, Risks, and Outlook
- [ ] Verifier quality, compute budgets, safety, reproducibility

---
_Every section claim must cite paper records from `data/papers.jsonl`._
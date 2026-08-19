# §2 Method: A Reproducible, Continuously-Updating Corpus Pipeline

> Draft v0.1 — every claim must eventually cite `data/papers.jsonl` records.
> This section documents the pipeline that *generates* this survey.

## 2.1 Design principles

1. **Deterministic and auditable.** Every structuring step is a keyword/regex
   rule, not an LLM call. A claim about a paper can be re-derived from its
   abstract and full text by anyone.
2. **Append-only evidence.** The paper database (`data/papers.jsonl`) is
   append-only; verification metadata is merged via atomic rewrites. The
   evidence chain runs from arXiv entry → structured record → survey claim.
3. **Living, not frozen.** A weekly cron sweeps the frontier; historical
   backfills cover 2023 onward. Sections cite the corpus *state*, and digests
   archive the evolving frontier.
4. **Honest about signal strength.** Abstract-level tags are signals;
   full-text verification is a separate gate. Only verified records may back
   survey claims.

## 2.2 Corpus construction

- **Sources**: the arXiv API (export.arxiv.org), six pillar queries over
  categories cs.AI, cs.LG, cs.CL, cs.CV, cs.CR, cs.MA, cs.DC, q-fin.
- **Windows**: weekly frontier sweep (last 21 days) + non-overlapping
  historical backfill windows (0–360, 360–720, 720–1080, 1080–2160 days).
- **Rate limiting & robustness**: ≥3s between requests, retries with backoff,
  time-boxed cache, and salvage of complete `<entry>` blocks from truncated
  responses.
- **Size**: 574 records (2023–2026) at the time of writing; 92 records
  records full-text verified.

## 2.3 Deterministic structuring

Each arXiv entry is mapped to a record with:

- **pillar** — the query of origin (six-pillar taxonomy);
- **methods** — 22 keyword families (RLVR/GRPO, Verifier/PRM, CoT, MCTS,
  MoE, distillation, quantization, KV cache, long context, preference
  optimization, interpretability, safety/jailbreak, multi-agent, tool use,
  memory/RAG, computer use, deep research, world models, video generation,
  VLM, quant/trading); short acronyms use word-boundary matching to avoid
  false positives (e.g. "cot" inside "scotland");
- **benchmarks** — a curated list (AIME, GSM8K, MATH, GPQA, SWE-bench,
  MMLU, ARC-AGI, AgentBench, GAIA, …) with word-boundary rules for short
  names;
- **models** — regex patterns for common model families;
- **key_results** — sentences carrying result markers (outperform, achieves,
  state-of-the-art, …).

## 2.4 Full-text verification (core-corpus gate)

- **Sources**: ar5iv (LaTeXML HTML) first; arXiv native HTML for papers ar5iv
  has not converted. arXiv abstract pages masquerading as fulltext are
  rejected by `ltx_` marker detection.
- **Procedure**: pull full text → re-run the deterministic taggers on it →
  record `verified` plus matched-method overlap vs. the abstract-level tags.
- **Status**: 92 records verified across all six pillars; source split ar5iv/arxiv-html
  recorded per record.

## 2.5 Citation tracking (in progress)

Semantic Scholar metadata (citationCount, influentialCitationCount) is
fetched per arXiv id and stored in `data/citations.jsonl`; anonymous access
degrades gracefully and records are only persisted on success.

## 2.6 Reproducibility artifacts

- `presearch` CLI (stdlib-only Python, ≥3.10): `weekly`, `backfill`,
  `verify`, `citations`, `db stats`, `survey`.
- GitHub Actions cron (weekly) commits new research back to the repository.
- MIT code, CC BY 4.0 data.

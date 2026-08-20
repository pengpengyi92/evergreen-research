# 🌲 P-Research

**Frontier research AI — a self-updating, ever-growing academic research system.**

Every week it sweeps arXiv for frontier papers and turns them into queryable,
verifiable, predictable research data: a living paper database · full-text
verification · citation tracking · direction clustering · research-group
radars · top-venue acceptance odds — and from all of it, a systematic survey
that keeps growing.

**Treat papers as data, research as quant, and the academic frontier as a market.**

- **Evergreen**: the corpus grows weekly; every survey claim traces back to a corpus record and never rots
- **Zero dependencies**: pure Python standard library, `python -m presearch.cli` just runs
- **Open**: MIT code + CC BY 4.0 data, auto-updated by GitHub Actions every week

## What it tracks (6 pillars)

1. **LLM Reasoning / Test-time Compute** — CoT, verifiers, RLVR, inference-time scaling
2. **Agentic AI / Deep Research Systems** — multi-agent, tool use, memory, computer use
3. **Efficient Training & Inference** — MoE, distillation, quantization, KV cache, scaling laws
4. **RL / Alignment / Safety** — preference optimization, interpretability, jailbreaks
5. **Multimodal / World Models** — VLM, video generation, world models, embodied AI
6. **Quant × AI** — LLM for trading, financial time-series foundation models

## Quickstart

```bash
# no dependencies beyond the Python standard library
python3 -m presearch.cli weekly --max-per-pillar 10

# or install the CLI
pip install .
presearch weekly
```

Outputs:

```text
data/papers.jsonl          # append-only structured paper records
data/weekly/2026-W34.md    # this week's frontier digest
data/index.md              # master index (auto-regenerated)
docs/index.md              # GitHub Pages landing (auto-regenerated)
```

Other commands:

```bash
presearch fetch --categories cs.AI,cs.CL --max 20 --days 7   # raw arXiv fetch
presearch backfill --windows 360-1080,1080-2160 --per-pillar 30  # historical backfill
presearch verify --pillar "LLM Reasoning / Test-time Compute" --top 40  # full-text verification
presearch db stats                                            # database statistics
presearch survey                                              # print the survey outline
```

### Full-text verification (M2)

`presearch verify` promotes papers toward the survey core corpus by pulling
their full text (ar5iv first, then arXiv native HTML for papers ar5iv has
not converted yet), re-running the deterministic taggers on full text, and
recording `verified` + matched-method metadata on each database record.
Only full-text-verified papers may back survey claims.

## How it works

```text
arXiv API (6 pillar queries)
  -> rate-limited fetch with retry + truncated-response salvage
  -> deterministic structuring (methods / benchmarks / models / result claims)
  -> append to data/papers.jsonl (idempotent, deduplicated)
  -> cross-pillar signal clustering
  -> weekly digest + index + survey outline update
```

Every step is deterministic and auditable — no closed-box LLM calls, no
hidden state. The evidence chain runs from an arXiv entry all the way to the
survey claim that cites it.

## 🔁 Our industry chain (the loop)

Research has an industry chain, and P-Research sits in its middle:

```
upstream              midstream (us)                downstream
papers · journals    →  P-Research terminal +      →  reports · surveys ·
conference papers       PRDT (structure → verify      papers · journal
experiments ·           → distill → research         submissions
research reports        graph → matrix/clusters)
        ↑_______________________________________________|
             feedback: published papers re-enter the upstream
             (our papers get indexed and cited, becoming raw
             material for others)
```

- **Upstream** is papers — journals, conference papers, experiments, research
  reports. arXiv is the largest open mine: upstream is free, but extracting it
  requires tools.
- **Midstream** is us — the P-Research terminal plus internal PRDT, the
  research-market's PDAT→PET.
- **Downstream** is our output — digests, the survey, system papers, Quant×AI papers.
- **The feedback loop** is unique to the academic market: in finance your trades
  never become market data, but in research your papers become data.
  **Publishing is re-entering the upstream.**

In one line: **we are both consumers and producers of data.**

## Honest limitations

- Evidence is **abstract-level** for unverified records: pillar assignment
  follows the query of origin, tags come from keyword/regex matching.
  92 records (across all six pillars) are full-text verified, with a 99%
  method-tag match rate on the first 45.
- Citation data (OpenAlex, keyless) covers older papers; recent papers
  rely on the citation-lag-immune novelty fallback.
- Treat all digests as **research signals, not verified facts**.

## Roadmap

- [x] v0.1 weekly pipeline (fetch -> structure -> cluster -> publish)
- [x] Historical corpus backfill (`presearch backfill`) — 500+ papers, 2023-2026
- [x] Full-text verification (`presearch verify`) — ar5iv + arXiv native HTML
- [x] Citation tracking (`presearch citations`) — keyless OpenAlex source (S2 optional)
- [x] Method-overlap novelty scoring (`presearch novelty`)
- [x] Automated citation audit (`presearch audit`) — 0 FAIL on the current draft
- [x] Checksummed snapshots (`presearch snapshot`) — Zenodo-ready archives
- [x] Survey draft v1 (7 sections) + compiled PDF (`data/survey/draft.pdf`)
- [x] RSS feed of weekly digests (`data/weekly/feed.xml`)
- [x] GraphRAG communities (`presearch graphrag`) + top-venue radar (`presearch predict`)
- [ ] Hostile human review (>= 2 reviewers) -> arXiv submission
- [ ] Python API (`pip install p-research`)

## Data license

- Code: MIT (see LICENSE)
- Data (`data/`): CC BY 4.0 — reuse it, cite us.

## 💬 Discussion zones

Nine public zones mapped to our research landscape — join any of them to
discuss, question, or challenge:

| # | Zone | Topic |
|---|------|-------|
| #2 | 🛡️ [ai-security](https://github.com/pengpengyi92/p-research/discussions/2) | the shadow of our three research lines: attacks / defenses / benchmarks |
| #3 | 🧠 [RAG](https://github.com/pengpengyi92/p-research/discussions/3) | retrieval memory — the spine of agents |
| #4 | 🧬 [Memory](https://github.com/pengpengyi92/p-research/discussions/4) | in-model memory: attention / KV cache / long context |
| #5 | 🔧 [Tool Use](https://github.com/pengpengyi92/p-research/discussions/5) | the hand: tools / skills / tool learning |
| #6 | 🗺️ [Planning](https://github.com/pengpengyi92/p-research/discussions/6) | the commander: goals / boundaries / workflows / harness |
| #7 | 📏 [Eval](https://github.com/pengpengyi92/p-research/discussions/7) | the judge: benchmarks / evaluation engineering |
| #8 | 🎯 [Research Interests](https://github.com/pengpengyi92/p-research/discussions/8) | our research-interest statement (the charter) |
| #9 | 🌌 [AGI](https://github.com/pengpengyi92/p-research/discussions/9) | the sky: AGI and the full AI chain |
| #1 | 📌 [Issue hub](https://github.com/pengpengyi92/p-research/issues/1) | proposals / corrections / new archives |

> The five capability zones (RAG / Memory / Tool Use / Planning / Eval) are
> the public curriculum of PAT's five elements; #8 is the charter, #9 is the
> sky, and #2 is the shadow across all of them.

## Contribute

See CONTRIBUTING.md. The single most valuable contribution is a rigorous
review of a weekly digest: challenge a claim, fix a tag, or verify a paper
by reading its full text.

Publishing roadmap (human steps only): see [LAUNCH.md](LAUNCH.md).

---

*P-Research is the public research output of the PRDT (Pengyi
Research Development Team) research intelligence program.*

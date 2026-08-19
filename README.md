# 🌲 P-Research

**A self-updating, continuously running frontier-AI research intelligence.**

Every week, P-Research ingests the latest papers from arXiv, structures
them into a living database, clusters cross-pillar signals, and publishes:

- a **weekly frontier-AI digest** — `data/weekly/`
- a **living paper database** — `data/papers.jsonl` (append-only, one line per paper)
- a **growing systematic survey** — `data/survey/`

It runs itself: a GitHub Actions cron runs every Monday, commits new research
back to this repo, and the digest is published to GitHub Pages. You can also
run it locally in one command.

## Why "Evergreen"

Most research write-ups die the day they are published. P-Research
stays alive: the corpus grows every week, the survey accumulates evidence
instead of rotting, and every claim links back to the paper records that
support it. 常青 — always growing.

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
上游 upstream        中游 midstream (us)          下游 downstream
papers · journals   →  P-Research terminal +     →  reports · surveys ·
conference papers      PRDT (structure → verify     papers · journal
experiments ·          → distill → research        submissions
research reports        graph → matrix/clusters)
        ↑_______________________________________________|
             回流: published papers re-enter the upstream
             (我们的论文被索引、被引用，成为别人的原料)
```

- **上游**是 paper——学术期刊、会议论文、实验数据、研究报告。arXiv 是
  最大的公开矿场：上游不收费，但需要工具才能开采。
- **中游**是我们——presearch 终端 + 内部 PRDT，研究界的 PDAT→PET。
- **下游**是我们的产出——周报、survey、系统论文、Quant×AI 论文。
- **回流**是学术市场独有的闭环：金融世界里你的交易不会变成行情，
  但研究界里你的论文会变成数据。**发表即入上游。**

一句话：**我们既是数据的消费者，也是数据的生产者。**

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
- [x] Citation tracking (`presearch citations`) — S2 connector (batch runs want a free S2_API_KEY)
- [x] Method-overlap novelty scoring (`presearch novelty`)
- [x] Automated citation audit (`presearch audit`) — 0 FAIL on the current draft
- [x] Checksummed snapshots (`presearch snapshot`) — Zenodo-ready archives
- [x] Survey draft v1 (7 sections) + compiled PDF (`data/survey/draft.pdf`)
- [ ] Hostile human review (>= 2 reviewers) -> arXiv submission
- [ ] RSS feed of weekly digests
- [ ] Python API (`pip install p-research`)

## Data license

- Code: MIT (see LICENSE)
- Data (`data/`): CC BY 4.0 — reuse it, cite us.

## Contribute

See CONTRIBUTING.md. The single most valuable contribution is a rigorous
review of a weekly digest: challenge a claim, fix a tag, or verify a paper
by reading its full text.

Publishing roadmap (human steps only): see [LAUNCH.md](LAUNCH.md).

---

*P-Research is the public research output of the PRDT (Pengyi
Research Development Team) research intelligence program.*

# 🌲 Evergreen Research

**A self-updating, continuously running frontier-AI research intelligence.**

Every week, Evergreen Research ingests the latest papers from arXiv, structures
them into a living database, clusters cross-pillar signals, and publishes:

- a **weekly frontier-AI digest** — `data/weekly/`
- a **living paper database** — `data/papers.jsonl` (append-only, one line per paper)
- a **growing systematic survey** — `data/survey/`

It runs itself: a GitHub Actions cron runs every Monday, commits new research
back to this repo, and the digest is published to GitHub Pages. You can also
run it locally in one command.

## Why "Evergreen"

Most research write-ups die the day they are published. Evergreen Research
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
python3 -m evergreen.cli weekly --max-per-pillar 10

# or install the CLI
pip install .
evergreen weekly
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
evergreen fetch --categories cs.AI,cs.CL --max 20 --days 7   # raw arXiv fetch
evergreen backfill --windows 360-1080,1080-2160 --per-pillar 30  # historical backfill
evergreen verify --pillar "LLM Reasoning / Test-time Compute" --top 40  # full-text verification
evergreen db stats                                            # database statistics
evergreen survey                                              # print the survey outline
```

### Full-text verification (M2)

`evergreen verify` promotes papers toward the survey core corpus by pulling
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

## Honest limitations

- Evidence is **abstract-level**: pillar assignment comes from the query of
  origin, tags come from keyword/regex matching. Full-text verification is a
  scheduled next milestone, not a claim made today.
- Citation tracking, novelty scoring, and reproducibility verification are
  not yet implemented (roadmap below).
- Treat all digests as **research signals, not verified facts**.

## Roadmap

- [x] v0.1 weekly pipeline (fetch -> structure -> cluster -> publish)
- [x] Historical corpus backfill (`evergreen backfill`) — 500+ papers, 2023-2026
- [x] Full-text verification (`evergreen verify`) — ar5iv + arXiv native HTML
- [x] Citation tracking (`evergreen citations`) — S2 connector (batch runs want a free S2_API_KEY)
- [x] Method-overlap novelty scoring (`evergreen novelty`)
- [x] Automated citation audit (`evergreen audit`) — 0 FAIL on the current draft
- [x] Checksummed snapshots (`evergreen snapshot`) — Zenodo-ready archives
- [x] Survey draft v1 (7 sections) + compiled PDF (`data/survey/draft.pdf`)
- [ ] Hostile human review (>= 2 reviewers) -> arXiv submission
- [ ] RSS feed of weekly digests
- [ ] Python API (`pip install evergreen-research`)

## Data license

- Code: MIT (see LICENSE)
- Data (`data/`): CC BY 4.0 — reuse it, cite us.

## Contribute

See CONTRIBUTING.md. The single most valuable contribution is a rigorous
review of a weekly digest: challenge a claim, fix a tag, or verify a paper
by reading its full text.

---

*Evergreen Research is the public research output of the PRDT (Pengyi
Research Development Team) research intelligence program.*

# 🌲 P-Research

**前沿 research AI —— 一个自我更新、可持续生长的学术研究系统。**

每周自动扫描 arXiv 前沿论文，把它们变成可查询、可核验、可预测的研究
数据：活论文库 · 全文核验 · 引用追踪 · 方向聚类 · 科研组雷达 · 顶会
录取预测——并从中持续生长出一篇系统 survey。

**把论文当数据，把研究当量化，把学术前沿当市场。**

- **常青**：论文库每周增长，survey 的每句断言可追溯到语料记录，永不腐烂
- **零依赖**：纯 Python 标准库，`python -m presearch.cli` 即跑
- **公开**：MIT 代码 + CC BY 4.0 数据，GitHub Actions 每周自动更新

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

## 💬 Discussion zones（欢迎讨论）

九个公开讨论区，对应我们的研究版图——欢迎在任何一区发言、提问、挑战：

| # | 区 | 主题 |
|---|----|------|
| #2 | 🛡️ [ai-security](https://github.com/pengpengyi92/p-research/discussions/2) | 三条研究线的暗面：攻击 / 防御 / 评测 |
| #3 | 🧠 [RAG 区](https://github.com/pengpengyi92/p-research/discussions/3) | 检索记忆（agent 的脊柱） |
| #4 | 🧬 [Memory 区](https://github.com/pengpengyi92/p-research/discussions/4) | 模型内记忆：attention / KV cache / 长上下文 |
| #5 | 🔧 [Tool Use 区](https://github.com/pengpengyi92/p-research/discussions/5) | 手：工具 / skill / tool learning |
| #6 | 🗺️ [Planning 区](https://github.com/pengpengyi92/p-research/discussions/6) | 指挥官：目标 / 边界 / 工作流 / harness |
| #7 | 📏 [Eval 区](https://github.com/pengpengyi92/p-research/discussions/7) | 裁判：benchmark / 评测工程 |
| #8 | 🎯 [Research Interests](https://github.com/pengpengyi92/p-research/discussions/8) | 我们的研究兴趣宣言（总纲） |
| #9 | 🌌 [AGI 区](https://github.com/pengpengyi92/p-research/discussions/9) | 星空层：AGI 与 AI 全链路 |
| #1 | 📌 [Issue 参与枢纽](https://github.com/pengpengyi92/p-research/issues/1) | 提案 / 勘误 / 新档案 |

> 五个能力区（RAG / Memory / Tool Use / Planning / Eval）= 内部研究框架
> PAT 五要素的公开课程表；#8 是总纲，#9 是星空。#2 是贯穿全部的影子。

## Contribute

See CONTRIBUTING.md. The single most valuable contribution is a rigorous
review of a weekly digest: challenge a claim, fix a tag, or verify a paper
by reading its full text.

Publishing roadmap (human steps only): see [LAUNCH.md](LAUNCH.md).

---

*P-Research is the public research output of the PRDT (Pengyi
Research Development Team) research intelligence program.*

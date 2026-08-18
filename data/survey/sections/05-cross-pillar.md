# §5 Cross-Pillar Convergence under a Compute-Allocation Lens

> Draft v0.1. Counts are abstract-level corpus frequencies (503 records);
> pillar assignment = query of origin. Verified subsets are noted where used.

## 5.1 Method families that refuse to stay in one pillar

A method family that appears in several pillars at once is either a fad, a
foundation, or a bridge. The corpus matrix (papers per pillar) for families
spanning ≥ 5 pillars:

| Family | Reasoning | Agents | Efficiency | RL/Align | Multimodal | Quant |
|---|---|---|---|---|---|---|
| RLVR / GRPO | 29 | 18 | 5 | 9 | 2 | 7 |
| Preference optimization | 14 | 1 | 8 | 24 | 17 | 4 |
| VLM | 7 | 3 | 8 | 4 | 57 | 2 |
| Interpretability | 8 | 4 | 5 | 31 | 2 | 7 |
| Memory / RAG | 9 | 8 | 16 | 2 | 5 | 9 |
| Deep Research | 4 | 8 | 1 | 1 | 3 | 7 |
| Safety / Jailbreak | 11 | 6 | 1 | 12 | 5 | 4 |
| Distillation | 3 | 1 | 37 | 1 | 5 | 3 |
| Video generation | 6 | 2 | 5 | 1 | 19 | 5 |

*Reading guide: rows are allocation strategies; columns are where compute is
spent. The table is generated from `data/papers.jsonl` and regenerated on
every sweep.*

## 5.2 RLVR is the lingua franca

RLVR/GRPO is the strongest convergence signal in the corpus: present in all
six pillars, 29 + 18 + 9 + 7 + 5 + 2 = 70 records. The recipe — optimize a
policy against a verifiable reward — no longer belongs to math reasoning.
Embodied agents (BATON), black-box agent harnesses (ClawGym II), and
on-chain/finance pipelines all adopt it. Under the compute-allocation lens,
RLVR is a *reward-side* allocation: you spend compute deciding what "good"
means, and the policy follows.

## 5.3 The efficiency pillar is the mirror image

Where reasoning spends compute at inference, efficiency spends it at design
time — distillation (37 records), quantization (27), MoE (12), KV-cache
work (7) — to *buy back* the inference budget. The two pillars are not
opposed; they are the same curve. Distillation from a reasoning teacher to
a cheap student is literally test-time-compute crystallized into weights.
This is the sharpest single observation of the compute-allocation lens,
and §6 quantifies it with trend data.

## 5.4 Memory and verifiers meet in the middle

Memory/RAG spans all six pillars (9/8/16/2/5/9) and verifier/PRM language
leaks from reasoning into efficiency and alignment. The mechanism is
shared: both are ways to *move compute out of the model* — into stored
context (memory) or into an external judge (verifier). Agents, long-context
models, and retrieval-augmented pipelines are the same allocation move at
different timescales.

## 5.5 Quant×AI as a convergence sink

Quant×AI hosts 56 quant/trading records but also imports the frontier
stack: RLVR (7), deep research (7), interpretability (7), memory (9),
video generation (5), preference optimization (4). Finance is where the
reasoning pillar's *verifiable reward* (P&L, risk limits, backtests) is
native — which makes it a natural stress test for §7's open problems.

## 5.6 Caveats

- Abstract-level tags overstate co-occurrence: a paper mentioning
  "safety" is not a safety paper. Full-text verification (§2.4) is the
  gate that turns these frequencies into citable claims; verified-subset
  versions of this table ship with the final draft.
- Pillar assignment follows the query of origin; cross-pillar numbers
  therefore measure *query overlap* plus true method migration. We report
  both effects rather than hiding either.

## 5.7 What §5 claims, once verified

1. RLVR/GRPO is the most widely shared method family across pillars.
2. Efficiency methods are the counter-allocation to test-time compute.
3. Memory and verifiers are the two dominant "out-of-model" compute moves.
4. Quant×AI is the frontier stack's most demanding verifiable-reward testbed.

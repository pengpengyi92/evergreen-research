# §7 Open Problems, Risks, and Outlook

> Draft v0.1. Open problems are ordered by how directly the corpus can
> test them.

## 7.1 Verifier quality is the new bottleneck

RLVR scales only as far as the reward signal is trustworthy. The corpus
already shows the failure mode migrating: verifier/guard-model audits
(`evg-204795ac0a18`), affective-hallucination diagnosis
(`evg-a1327781cf59`), and black-box agent-harness RL (`evg-e804bfb18640`)
all circle the same question — **how do you verify the verifier?**
Candidate research directions: adversarial verifier evaluation, reward
calibration under distribution shift, and process-reward attribution over
long traces.

## 7.2 Test-time compute: lever or budget?

§4.4 asked whether the frontier treats test-time compute as a lever (spend
more when it helps) or a budget (fixed envelope). The corpus cannot answer
it yet — scaling-law papers are under-represented in our queries, and the
formal literature lives in the surveys we cite (`arXiv:2501.02497`,
`arXiv:2505.07178` ⚠). A corpus upgrade (dedicated scaling-law query
family) is planned.

## 7.3 The closed frontier is invisible to us

Closed commercial systems (o-series, Claude, Gemini reasoning modes)
publish no full text; our corpus sees them only through third-party
evaluations. Any survey claim about "the frontier" is therefore
conditional on the open literature. Mitigation: position claims as
"open-literature frontier" and track closed-model evaluations as a
separate, clearly-labeled source class.

## 7.4 Citation lag and novelty scoring

2026 papers have immature citation graphs; Semantic Scholar coverage lags
submission by weeks. Novelty scoring from citations (§2.5) must therefore
blend citation counts with *method-overlap novelty* (how unusual a
paper's method vector is within its pillar cohort) — a direction we are
implementing.

## 7.5 Reproducibility of a living artifact

A "living survey" is only as living as its hosting. Risks: repo
abandonment, API changes, DB corruption. Mitigations in progress: full
DB checksums in digests, deterministic regeneration from raw arXiv
responses (cached), and periodic Zenodo snapshots of `data/`.

## 7.6 Publication risk (arXiv endorsement)

First-time submissions to cs.AI/cs.LG/cs.CL require endorsement, and arXiv
tightened its policy in January 2026. Status and fallback venues are
tracked in `positioning.md`; the survey's substance is designed to remain
valuable regardless of venue (open data + code + digests).

## 7.7 Outlook

Three bets close the survey:

1. **Reward-side compute** (RLVR + verifiers) keeps diffusing into every
   pillar — Quant×AI is its most demanding testbed because P&L is the
   harshest verifier.
2. **Efficiency methods become reasoning methods' mirror**: distillation
   crystallizes test-time compute into weights; the two pillars converge
   on one allocation curve.
3. **Memory and verifiers merge**: the next reasoning stack will treat
   stored context and external judges as one out-of-model compute
   substrate.

The corpus will re-test these bets every Monday.

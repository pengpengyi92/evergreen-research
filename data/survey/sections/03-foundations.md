# §3 Foundations: From Chain-of-Thought to RLVR

> Draft v0.1. `evg-*` ids cite Evergreen corpus records; only
> full-text-verified records are cited as evidence.

## 3.1 Chain-of-thought as the seed

Chain-of-thought (CoT) prompting showed that allocating inference tokens to
intermediate reasoning improves accuracy without touching weights. In our
verified corpus, CoT language appears in 2 verified 2024 papers and 12
verified 2025 papers — but increasingly as a *substrate* of learned
reasoning rather than as a prompting trick: reasoning traces became the
object of optimization, not just an artifact of prompts.

## 3.2 Verifiable rewards

The RLVR recipe — reinforcement learning where the reward is a
mechanically checkable function (a final answer, a unit test, a compiler
verdict) — removes the need for a learned reward model on many tasks.
Verifier/process-reward-model methods grow in the verified corpus from 1
(2024) to 9 (2025) to 5 (partial 2026). Representative verified records:

- `evg-e04110c6e72bd0da` (arXiv:2408.15565, 2024): self-improving code-assisted
  mathematical reasoning — an early bridge between code execution and
  verifiable rewards.
- `evg-a1327781cf590ac8` (arXiv:2508.16921, 2025): reward/verifier machinery
  applied beyond math, to affective-alignment diagnosis — a sign of the
  stack spreading across pillars.

## 3.3 GRPO, PPO, and the policy-optimization zoo

Within RLVR, group-relative policy optimization (GRPO) became the
workhorse because it drops the critic model, cutting memory and compute —
an *efficiency* choice that doubles as an *allocation* choice (reward vs.
representation). Our corpus shows preference-optimization language in 3
verified 2024 papers, 20 verified 2025 papers, and 7 in 2026 — the fastest
growth of any method family in the verified subset. Policy optimization now
appears far outside its origin: in embodied robot manipulation
(`evg-4e48d42ef4f7ad7e`, BATON), in inverse RL for control (`evg-3f12f30b5bc710da`),
and in dialogue model-based RL (`evg-964669cd2625570d`).

## 3.4 Search and self-correction

Test-time search (MCTS-style tree search, beam variants, best-of-N) turns
inference into an optimization loop over candidate traces. Verified
examples: `evg-4e48d42ef4f7ad7e` (subtask-level exploration composed into
long-horizon plans), `evg-37a3465e623bd6ff` (AutoSR: symbolic regression by
searching "research states"), `evg-6742b060cb568d54` (Le Critique:
privileged value functions guiding LLM reinforcement learning), and
`evg-f945ded0c59d6837` (PuzzleJAX, a benchmark designed for
reasoning-and-learning under search). Search methods in the verified corpus
grow 1 (2024) → 6 (2025) → 3 (partial 2026).

## 3.5 Reward hacking and the verifier-quality wall

As verifiable rewards scale, so does gaming them. The safety pillar already
feeds back into reasoning: verified record `evg-204795ac0a186819` (What Do
Compliance Detectors Read?) audits activation probes and guard models —
detector *representations* are now part of the reasoning stack's failure
modes. We flag an open problem here: **verifier quality is the new
bottleneck** — a claim we develop with corpus evidence in §7.

## 3.6 What the corpus shows

| Method family (verified full-text) | 2024 | 2025 | 2026 (partial) |
|---|---|---|---|
| RLVR / GRPO | 4 | 18 | 6 |
| Preference optimization | 3 | 20 | 7 |
| Chain-of-thought | 2 | 12 | 4 |
| Verifier / PRM | 1 | 9 | 5 |
| Search / MCTS | 1 | 6 | 3 |
| Test-time scaling | 0 | 7 | 5 |

*Corpus caveat: weekly sweeps weight recent years; 2026 is a partial year.
These are corpus frequencies, not field-wide prevalence.*

## 3.7 Open threads for §4

- How do verifiers and search interact with *inference-time scaling laws*?
- Where does the budget go — trace length, search width, or verifier depth?
- What transfers from the reasoning pillar to agents, efficiency, and
  quant×AI (§5)?

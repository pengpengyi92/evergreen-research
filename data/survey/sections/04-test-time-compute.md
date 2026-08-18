# §4 Test-Time Compute

> Draft v0.1. `evg-*` ids cite Evergreen corpus records (full-text verified
> unless noted). Formal scaling-law results are summarized from the survey
> literature; corpus evidence covers the *system designs*.

## 4.1 The allocation question

Test-time compute is the budget a model spends at inference — on tokens,
candidate traces, verifier calls, or tool interactions — to raise answer
quality without touching weights. The design space decomposes into three
questions we use to organize this section:

1. **Where does search happen?** — tree search, beam variants, best-of-N,
   or learned routing over candidate traces.
2. **What judges a trace?** — outcome verifiers, process reward models,
   learned value functions, or external tools.
3. **How does the budget scale?** — inference-time scaling laws and the
   regime where more compute stops helping.

## 4.2 Search: from fixed traces to composed plans

Verified corpus examples show search moving from "sample many answers" to
"search over structured states":

- `evg-4e48d42ef4f7ad7e` (BATON) — subtask-level exploration: each subtask is
  explored in a cheap short-horizon regime, and long-horizon trajectories
  are *composed* from stored solutions, turning multiplicative exploration
  cost (T to the power K) into additive (T times K).
- `evg-37a3465e623bd6ff` (AutoSR) — symbolic regression framed as searching
  "research states", with a verifier-governed transition model.
- `evg-6742b060cb568d54` (Le Critique) — privileged value functions steer LLM
  policy search, reintroducing critic-shaped guidance into the RLVR loop.
- `evg-f469e87d0194dc45` (Learning from Diverse Reasoning Paths) — routing and
  collaboration across diverse reasoning paths rather than single-trace
  decoding.
- `evg-f945ded0c59d6837` (PuzzleJAX) — a benchmark built for reasoning *and
  learning* under search, i.e. search as a first-class evaluation axis.

Reading: search is absorbing the *planning* role that classical AI assigned
to planners — but now the search space is language traces and the value
function is a learned or verifiable judge (§4.3).

## 4.3 Verifiers and process reward models

The judge is the new bottleneck (§3.5). Verified examples:

- `evg-58ed686e9dc31903` (GRIP) — grounded reasoning via
  information-restricted premises: restricting what a trace may assume is
  itself a verifier mechanism.
- `evg-e804bfb18640fc6e` (ClawGym II) — black-box RL on an agent harness: the
  environment as the ultimate verifier for agentic policies.
- `evg-204795ac0a186819` (Compliance Detectors) — audits of activation probes
  and guard models; detector *representation* quality becomes part of the
  reasoning stack's failure modes.

For the formal taxonomy of outcome vs. process reward models and their
failure modes (reward hacking, credit assignment over long traces), the
reader should consult `arXiv:2501.09686` and `arXiv:2501.02497`; our corpus
contributes the empirical observation that verifier-style machinery now
appears in 15 verified lead-pillar records — and in guard-model audits far
outside math reasoning.

## 4.4 Inference-time scaling laws

The quantitative literature (compute-optimal inference, budget
allocation, self-refinement limits) is summarized by the test-time-compute
survey `arXiv:2501.02497`; several more recent scaling-law surveys exist,
and we cite only ids verified against the live arXiv API.
Our corpus's contribution is *systemic* rather than formal: verified
records show test-time-scaling language in 7 papers from 2025 and 5 from
the partial year 2026 — and, importantly, it has begun to span pillars
(lead: 3, efficiency: 1, quant: 1 at abstract level). The scaling-law
question we can now ask the corpus: **does the frontier treat test-time
compute as a lever (spend more when it helps) or a budget (allocate a fixed
envelope)?** — a question flagged for §7.

## 4.5 Summary

| Mechanism | Verified examples | What it allocates |
|---|---|---|
| Structured search | BATON, AutoSR, Le Critique | trace space × time |
| Verifier / PRM | GRIP, ClawGym II, Compliance Detectors | judge quality |
| Routing/collaboration | Diverse Reasoning Paths | width vs. depth |
| Benchmark pressure | PuzzleJAX | evaluation budget |

*All records full-text verified; see §2.4 for the verification procedure.*

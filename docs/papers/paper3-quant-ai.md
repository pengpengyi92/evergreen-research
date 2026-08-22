# Agent-Native Trading Systems: A Corpus-Grounded Study of the Quant×AI Frontier — Where the Agent Loop Meets the Risk Layer

> **Draft v0.1 (assembled 2026-08-19)** — living paper of the PRDT / P-Research
> program. The corpus numbers in this draft are claims about the P-Research corpus
> snapshot (503 papers, 2023-2026; Quant×AI pillar 103 papers, 10 full-text verified)
> as of 2026-08-18. The live corpus grows weekly — every number here re-derives from
> `data/papers.jsonl` in this repository. The markdown is the living source;
> venue-targeted PDFs are compiled per submission. License: CC BY 4.0 (text) — reuse
> it, cite us.
>
> *A companion paper, "PRDT: Research as a Quant Problem" (`paper2-prdt-system.md`),
> describes the corpus pipeline this study is built on.*

---

# 1 Introduction

## 1.1 Trading as the verifiable-reward testbed

Trading is the most demanding verifiable-reward testbed for agentic AI. The
reward function (P&L), the constraints (risk limits), and the evaluation (the
market) are all external, quantitative, and unforgiving: an agent cannot argue
with a drawdown. This makes trading the natural stress test for the current
generation of autonomous systems — and, we will argue, the natural proving
ground for the agentic paradigm as a whole.

## 1.2 A corpus observation

The observation that motivates this paper comes from the P-Research corpus, a
continuously-updating, evidence-linked database of frontier-AI papers (503
records, 2023-2026, six-pillar taxonomy; see the companion system paper). The
Quant×AI pillar — LLM and agentic methods for trading and financial time
series — is the fastest-growing pillar in the corpus: at the time of writing
it holds **103 papers**, and the partial year 2026 (33 records) already
exceeds every previous full year. The frontier is building trading agents
faster than it builds anything else — and, on the development side, faster
than it builds their risk layers.

## 1.3 The gap

The development side tells the same story in sharper form. The open-source
frontier has productized the agent loop — market data access, tool
registries, memory, autonomous research→decide→execute cycles — into
downloadable systems with hundreds of thousands of stars. What these systems
carry, to the extent visible from public metadata and structure, is almost
none of the risk layer that institutional quantitative practice treats as
non-negotiable before capital is exposed: backtest hygiene, cost modeling,
capacity limits, hard risk constraints, and attribution. The loop exists; the
risk layer does not.

## 1.4 The thesis: a two-way exchange

Our thesis is that the two traditions need each other precisely where they are
weakest. Quant discipline supplies the missing risk layer for trading agents —
sharpened rewards, structural constraints, backtest hygiene, per-decision
attribution. Agentic capabilities supply the missing reading and reasoning
layer for quant stacks — unstructured-data ingestion, research automation,
execution as tool use, and decision traces as compliance substrate. The
synthesis is architectural, not rhetorical: an agentic loop wrapped in a
structural constraint layer, evaluated by a standardized harness that measures
discipline rather than returns.

## 1.5 Contributions

1. A corpus-grounded landscape of the Quant×AI frontier (§2): method imports,
   benchmark visibility, and a verified subset (n=10), all re-derivable from
   the public corpus.
2. A development-side study of agent-native trading systems (§3): what the
   HKUDS radar shows about how the open frontier productizes agency before
   risk.
3. A precise catalog of what quant discipline contributes to trading agents
   (§4) and what agent capabilities contribute to quant stacks (§5).
4. The specification of a quant-grade evaluation harness for open trading
   agents (§6): four checks — strategy drift, cost sensitivity, drawdown
   behavior, tool-use failure modes — reporting behavioral and disclosure
   scores, on public data only.

## 1.6 Scope and honesty

This paper measures behavioral risk properties of open research artifacts; it
is not investment advice, and the harness does not rank agents by
profitability. The market verifies returns; this paper builds the rig that
verifies discipline.

---

# 2 Corpus-Grounded Landscape

## 2.1 The Quant×AI pillar at a glance

The P-Research corpus tracks the Quant×AI pillar with a dedicated arXiv
query plan (q-fin.TR / q-fin.ST / q-fin.CP / cs.LG). At the time of
writing: **103 papers**, with year distribution 2023 (26), 2024 (20),
2025 (24), 2026 (33) — the only pillar in which the partial year 2026
already exceeds every previous full year. Growth itself is a finding:
the quant×AI frontier is accelerating.

## 2.2 Method composition (abstract level)

The dominant self-tag is, unsurprisingly, trading language (60 records).
What matters more is what the frontier *imports*: Memory/RAG (10), Deep
Research (8), RLVR/GRPO (8), Interpretability (7), video generation (5),
preference optimization (4). Three imports deserve emphasis:

- **RLVR/GRPO (8)**: verifiable rewards are native to trading — the
  reasoning pillar's training recipe finds its most natural testbed here
  (§2.4).
- **Memory/RAG (10)**: market context (news, filings, order books) is the
  canonical long-tail retrieval problem.
- **Deep Research (8)**: autonomous research loops are being pointed at
  markets, not just papers.

## 2.3 Benchmarks are nearly invisible

Abstract-level benchmark mentions in the pillar are sparse (MATH 8,
GSM8K 1, WebArena 1). This is not an absence of evaluation — it is the
survey's benchmark-visibility asymmetry in its strongest form: quant
papers evaluate on private or bespoke datasets (returns, Sharpe, hit
rates) that never surface in abstracts, while NLP-style benchmarks do.
The pillar's evaluation layer is therefore systematically opaque to
abstract-level mining — a measurement problem in itself.

## 2.4 Verified subset (n=10)

Full-text verification of the pillar's top papers confirms the import
pattern: Quant/Trading (8), Interpretability (5), Preference Optimization
(5), Memory/RAG (4), Safety/Jailbreak (4), RLVR/GRPO (3), Computer Use
(3), Deep Research (3). Two observations:

1. **Interpretability and safety co-occur with trading at full-text
   level** — the verified quant papers are concerned with *why* the model
   trades and *whether it can be trusted*, not merely with returns.
2. **Computer Use appears in the verified subset** — trading agents are
   beginning to operate interfaces (dashboards, terminals), not just
   APIs.

## 2.5 Cross-pillar position

In the verified cross-pillar matrix (n=92), Quant×AI is a *sink*: it
imports RLVR, memory, deep-research, and interpretability methods from
the reasoning and agentic pillars, and exports almost nothing back except
its signature property — verifiable reward design. That asymmetry is the
thesis of this paper: **trading is where agentic methods go to be tested
against reality.**



# 3 Agent-Native Trading Systems: The Development Side

## 3.1 The HKUDS radar as a case study

The P-Research group radar tracks the HKU Data Intelligence Lab's public
GitHub organization (92 repositories, 355K stars, 54 active in 2025+).
Three repositories define its trading line:

| Repo | Stars | Positioning |
|------|-------|-------------|
| Vibe-Trading | 31K | "Your Personal Trading Agent" |
| AI-Trader | 21K | "100% Fully-Automated Agent-Native Trading" |
| ClawWork | 8.3K | "OpenClaw as Your AI Coworker — $15K earned in 11 hours" |

What "agent-native trading" means in practice, reading across these
repositories: an LLM agent wrapped around market data access, a tool
registry (broker APIs, news, memory stores), an autonomous loop
(research → decide → execute), and a human-readable decision trace.
The engineering emphasis is on *agency* — the agent does the loop — and
the marketing emphasis is on *autonomy* ("fully-automated").

## 3.2 The gap: where is the risk layer?

Institutional quantitative practice treats a set of components as
non-negotiable before any capital is exposed: backtest hygiene
(lookahead avoidance, survivorship handling), cost modeling (slippage,
fees, market impact), capacity limits, risk limits as hard constraints,
and attribution of P&L to decisions rather than luck.

The agent-native repositories, to the extent visible from public
metadata and structure, center none of these. The loop exists; the risk
layer does not. The "personal trading agent" framing confirms the
boundary: these systems are built for individual users, where the
verifier is the user's own account balance over a short horizon — not a
risk desk.

This is not a criticism of the repositories. It is a structural
observation: **the open-source frontier has productized the agent loop
before productizing the risk layer, because the loop is exciting and the
risk layer is boring.** The boring layer is precisely what the quant
tradition has spent decades building.

## 3.3 What quant discipline would add (preview of §4)

- **Verifiable reward design**: P&L is verifiable but pathological —
  sparse, noisy, non-stationary, and gamed by luck. Quant practice
  sharpens it (risk-adjusted, cost-adjusted, benchmark-relative).
- **Hard constraints**: risk limits as constraints on the action space,
  not suggestions in the prompt.
- **Backtest hygiene**: the agent's "research" step needs the same
  lookahead discipline as any factor pipeline.
- **Attribution**: decision traces are not attribution; the agent's
  memory must be auditable per-decision.

## 3.4 The measurement rig (preview of §6)

Neither side currently measures the other. We propose a standardized
evaluation harness — quant-grade checks applied to open trading agents —
as the empirical contribution of this paper: strategy drift under market
regime change, cost sensitivity, drawdown behavior, and tool-use failure
modes, all on public data, all reproducible.



# 4 What Quant Discipline Can Contribute to Trading Agents

If §3's gap analysis is right — the agent loop exists, the risk layer
does not — then the contribution of the quant tradition is precise: it
is a catalog of *boring components* that turn an autonomous loop into a
defensible one. Four matter most for agent-native systems.

## 4.1 Verifiable reward design

P&L is the most verifiable reward an agent can have, and the worst one
to optimize naively: it is sparse, noisy, non-stationary, and heavily
confounded by luck and regime. Quant practice does not reject P&L — it
sharpens it into a family of risk-adjusted, cost-adjusted,
benchmark-relative objectives (Sharpe, information ratio, drawdown
ratios, turnover-adjusted returns). An agent-native trading system that
rewards "the trade made money" is training on noise; one that rewards
"the trade made money relative to its benchmark, after costs, within
limits" is training on signal. The reward function is the interface
between the two traditions, and it is currently the weakest seam in the
open repositories.

## 4.2 Hard constraints, not prompt suggestions

Risk limits in quant are constraints on the action space: position
caps, exposure budgets, stop regimes, kill switches. Prompted agents
obey constraints the way humans obey diet advice — probabilistically.
The quant contribution is architectural: wrap the agent's action space
with a constraint layer that *cannot* be violated by any generated
action (order validation, pre-trade checks, position reconciliation).
This is not a prompt-engineering problem; it is a system-boundary
problem. An agent-native system needs both the loop and the cage.

## 4.3 Backtest hygiene for the agent's "research" step

Every trading agent contains an implicit backtest: the agent researches
a strategy, reasons about it, and deploys it. Quant tradition has a
century of scar tissue about this step — lookahead bias, survivorship
bias, overfitting to regimes, ignoring costs and capacity. The agent's
research step inherits all of these risks and adds one of its own: the
agent *reads its own training data* (LLM pre-training includes market
discourse). Backtest hygiene for agents means: frozen evaluation
windows, out-of-sample discipline, cost modeling at decision time, and
explicit regime labels — the same checklist, applied to a decision-maker
that is harder to audit than a factor.

## 4.4 Attribution as the missing interpretability

The agent-native pitch is "explainable decision traces" — the agent
writes down why it traded. A decision trace is not attribution: it does
not tell you whether the *reason* caused the *profit*. Quant attribution
decomposes P&L into factors, timing, and selection, and asks which
decisions earned their risk. The trading agent's memory should be
subject to the same decomposition: which of the agent's beliefs, when
acted on, actually paid — and which were noise the trace dressed up as
signal. Attribution is interpretability with a cost basis; agents
currently ship the former without the latter.

## 4.5 Summary

| Quant component | Agent-native translation |
|-----------------|--------------------------|
| Sharpened reward | risk/cost/benchmark-adjusted objectives, not raw P&L |
| Risk limits | hard constraint layer around the action space |
| Backtest hygiene | frozen windows + cost modeling for the research step |
| Attribution | per-decision P&L decomposition of the agent's memory |



# 5 What Agent Capabilities Can Contribute to Quant

The exchange is not one-directional. Quant stacks have their own
bottlenecks that agentic capabilities are well-positioned to break.
Four stand out, ordered by how far the open frontier has already come.

## 5.1 Unstructured data ingestion

Quant's historical edge was structured data: prices, volumes, balances.
The modern edge increasingly lives in unstructured sources — filings,
calls, news, social sentiment, satellite and shipping data — which
factor pipelines ingest only after expensive, brittle processing.
Language models invert the cost curve: reading a filing and extracting a
structured event is now the cheap part. The agent-native contribution is
a *reading layer*: an auditable, schema-validated pipeline from raw
document to structured feature. (This is the same pattern P-Research
applies to papers — the research-market and the trading-market data
problems are structurally identical.)

## 5.2 Research automation

A quant desk's research loop — hypothesize, gather evidence, test,
attribute, document — is expensive per unit of human attention.
Agentic research systems (the deep-research family the P-Research corpus
tracks: 8 imports in the Quant×AI pillar alone) automate the *gathering
and organizing* while leaving the *judgment* human. The defensible
division of labor is exactly PRDT's: deterministic evidence pipelines
with an audit layer, humans at the hypothesis and sign-off gates.
Research automation does not replace researchers; it raises the quality
floor of what reaches them.

## 5.3 Execution as tool use

Execution is already the agent's natural interface: brokers expose APIs,
and tool-calling is the agent-native way to reach them. The open
systems demonstrate the loop; what they have not yet demonstrated is
*execution quality* under the §4 checklist. The contribution to quant
here is architectural vocabulary — tool registries, capability schemas,
memory hierarchies — that factor stacks can adopt for their own
automation layers without adopting the agent's autonomy assumptions.

## 5.4 Explainable decision traces as a compliance asset

Quant firms operate under explainability pressure (regulators, risk
committees, investors) that classic ML stacks meet with
post-hoc interpretability. Agentic traces — the model's own written
reasoning — are a *new input class* for that obligation: not a
replacement for attribution (§4.4), but a richer substrate for it.
A decision trace attached to a position, then decomposed against
realized P&L, is the beginning of a compliance-grade audit trail that
was previously impossible.

## 5.5 The two-way street, stated

Quant gives agents the risk layer they lack; agents give quant the
ingestion and reasoning layer it has never had. The synthesis is not
"an LLM that trades" but a stack where the loop is agentic and the
constraints are structural:

> **Agentic AI is the interface. Quant discipline is the risk layer.
> The market is the verifier.**



# 6 The Evaluation Harness

The empirical contribution of this paper is a standardized, quant-grade
evaluation harness for open trading agents — the missing risk layer from
§3.2, delivered as a measurement rig rather than as a trading system.
This section specifies its design; the implementation ships as an open
plugin against the P-Research corpus pipeline.

## 6.1 Design principles

1. **Public data only.** No proprietary market data in the harness;
   results must be reproducible from the same inputs by any reviewer.
2. **Agent-agnostic interface.** The harness evaluates any trading agent
   through a thin adapter: `observe(state) -> decisions`, where a
   decision is a trade intent with a written rationale. The agent's
   internals are a black box; its *behavior* is the test subject.
3. **Checks, not leaderboards.** The harness does not rank agents by
   return. It reports pass/fail on risk-relevant properties, the way a
   risk desk files exceptions, not the way a Kaggle board ranks entries.
4. **Failure modes are first-class outputs.** A check that fails with a
   clean diagnosis is more valuable than a return that impresses.

## 6.2 The four checks

**C1 — Strategy drift under regime change.** Run the agent over
segmented market regimes (bull / bear / high-volatility / low-liquidity,
constructed from public index data). Measure whether the agent's stated
strategy — extracted from its own decision rationales — drifts with the
regime. A pass: stated strategy is regime-stable even when realized
returns are not. This checks whether the agent *knows what it is doing*
under distribution shift.

**C2 — Cost sensitivity.** Replay the same decisions at escalating cost
assumptions (spread + slippage + fees, 0 → 10 → 30 bp). A pass: the
agent's edge survives its stated cost model, and its decision volume
falls as costs rise (cost-awareness), rather than trading through the
costs (cost-blindness).

**C3 — Drawdown behavior.** Measure realized drawdown sequences against
the agent's own risk statements. A pass: the agent reduces exposure
after exceeding its stated drawdown threshold, and its rationale logs
acknowledge the drawdown state. This checks whether stated risk limits
are behavior, not decoration.

**C4 — Tool-use failure modes.** Inject tool failures (broker API
errors, stale market data, memory retrieval misses) at controlled rates.
A pass: the agent detects the failure, retries or degrades explicitly,
and never emits a trade based on data it has flagged as stale. This
checks the seam where agentic autonomy meets operational reality.

## 6.3 Metrics and thresholds

Each check emits two numbers: a **behavioral score** (measured) and a
**disclosure score** (does the agent's own trace acknowledge the
situation?). The harness reports the pair — behavior without disclosure
is a silent failure; disclosure without behavior is decoration. Pass
thresholds are set conservatively and published with the harness, so
"passing" is a falsifiable claim any reviewer can re-derive.

## 6.4 Implementation status and plan

The harness is specified here; implementation is staged as a
P-Research-ecosystem plugin:

1. Adapter spec + public data bundles (regime segmentation of index
   data, synthetic cost ladders, failure-injection proxy).
2. Reference runs against open agents (the HKUDS trading line is the
   natural first cohort, with authors' consent).
3. Results published as machine-readable reports in the same
   append-only style as the corpus — the research-market version of a
   risk report.

## 6.5 Scope honesty

The harness measures *behavioral risk properties*, not profitability,
and not whether an agent "should" be traded with real capital. It is a
risk desk for open research artifacts, not investment advice. The line
is drawn deliberately: the market is the verifier of returns; this
harness is the verifier of discipline.



# 7 Conclusion

This paper began from a corpus observation: the Quant×AI pillar is the
only one in which the partial year 2026 already exceeds every previous
full year, and the open frontier is building trading agents faster than
it is building their risk layers. We traced the landscape on both sides
of the exchange — 103 corpus papers with their method imports, and the
development-side reality of agent-native repositories with hundreds of
thousands of stars and no backtest-grade discipline.

The argument, in one sentence: **the two traditions need each other
precisely where they are weakest.**

- Trading agents lack the boring layer — sharpened rewards, hard
  constraints, backtest hygiene, attribution — that institutional quant
  spent decades building.
- Quant stacks lack the reading and reasoning layer that agentic
  capabilities now make cheap — unstructured ingestion, research
  automation, execution as tool use, decision traces as compliance
  substrate.

The proposed synthesis is architectural, not rhetorical: an agentic
loop wrapped in a structural constraint layer, evaluated by a
standardized harness that measures discipline rather than returns.
P-Research supplies the measurement rig — the same deterministic,
append-only, audited infrastructure that tracks the research frontier
is repurposed to track the trading-agent frontier, because the two
frontiers are converging on the same question:

**Who verifies the verifier?**

The market verifies returns. The risk layer verifies discipline. The
harness verifies the risk layer. And the whole stack — like every claim
in this paper — remains open, reproducible, and subject to the same
weekly audit as the corpus that generated it.

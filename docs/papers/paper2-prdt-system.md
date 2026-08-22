# PRDT: Research as a Quant Problem — An AI-Native Research Intelligence Framework

> **Draft v0.1 (assembled 2026-08-19)** — living system paper of the PRDT / P-Research
> program. The corpus numbers in this draft are claims about the P-Research corpus
> snapshot (503 papers, 2023-2026; 92 full-text verified) as of 2026-08-18. The live
> corpus grows weekly — every number here re-derives from `data/papers.jsonl` in this
> repository. The markdown is the living source; venue-targeted PDFs are compiled per
> submission. License: CC BY 4.0 (text) — reuse it, cite us.
>
> *A companion paper, "Agent-Native Trading Systems" (`paper3-quant-ai.md`), applies
> the framework's corpus to the Quant×AI frontier.*

---

# 1 Introduction

## 1.1 The research-as-market thesis

Quantitative finance treats markets as data and converts raw price streams
into factors, portfolios, backtests, and risk reports. This paper proposes
that the research frontier admits the same treatment, with a materially
better starting position: the market data — papers, citations, code, and
institutional affiliations — is public by default.

Under this lens, the mapping is direct. A paper is a data point with
high-dimensional features (methods, benchmarks, models, citations). A
method family is a factor whose momentum can be measured week over week.
A survey is a portfolio: claims are positions, each backed by evidence
and sized by confidence. A citation audit is risk control. And the
researcher's alpha is the same as a quant's: seeing structure earlier and
more reproducibly than the market does.

The thesis is most tractable in CS/AI. Papers ship code, so "backtesting"
a claim means running the released repository. The feedback loop is
weekly — arXiv updates every day. And unlike trading, the evidence chain
is free: every claim can be traced from survey text to database record to
original manuscript, with no proprietary data in between.

## 1.2 Why deterministic infrastructure (and not another agent)

LLM research agents are increasingly capable, but they inherit the
stochasticity of their substrate: two runs produce two answers, and
"reasoning" is not auditable in the sense risk control requires. PRDT
takes the opposite design position: **the pipeline itself contains no LLM
calls**. Ingestion, structuring, verification, clustering, and auditing
are deterministic programs with schema-validated outputs. LLMs are — by
design — kept outside the evidence chain, reserved for the human-readable
synthesis layers where judgment, not reproducibility, is the goal.

This buys three properties that agents cannot yet claim:
1. **Auditability**: every claim re-derives from raw inputs.
2. **Reproducibility**: the same corpus state produces the same survey.
3. **Honest signal strength**: abstract-level tags are labeled as such;
   only full-text-verified records may back survey claims.

## 1.3 The two-track architecture

PRDT ships as two coordinated systems rather than one monolith:

- **PRDT (internal)**: the five-agent research loop, research graph, and
  hypothesis/experiment engines — the private "strategy" layer, where
  hypotheses, contradictions, and internal conclusions live.
- **P-Research (public)**: the product layer — a weekly-sweeping corpus
  pipeline with verification, citation tracking, group radars, a
  high-dimensional paper matrix, and the living survey it generates.

The echo between them mirrors the quant pattern of private funds and
public indices: the public layer thickens the data, attracts
collaborators, and earns reputation; the private layer consumes that
corpus to do deeper, opinionated research. Neither competes with the
other; they compound.

## 1.4 Contributions

1. A five-agent, domain-agnostic research intelligence framework with a
   research graph and domain-aware association/contradiction/hypothesis
   engines (Section 3).
2. Robustness engineering for the public scholarly data layer:
   truncated-response salvage, dual-source full-text verification, keyless
   citation fallback, fail-fast rate-limit circuits (Section 4).
3. An evaluation of the running system over a 503-paper corpus, including
   a 99% tag-match verification rate and an automated audit that has
   caught 24 mechanical citation errors pre-review (Section 5).
4. Evidence that the framework's flagship output — a living, audited
   survey — is itself a research contribution, not just a product (Section 6).

## 1.5 Scope and honesty

This is a systems paper about infrastructure, not a claim that research
is solved. The system's limitations are enumerated in Section 7: the
corpus sees only the open literature; full-text coverage is a fraction
of the database; recent papers suffer citation lag; and the final
publishing gates — human review and endorsement — remain, by design,
outside the machine.



# 2 Design Principles

PRDT is a systems position paper as much as a system description. Four
principles separate it from both "paper database + LLM wrapper" tools and
from pure agent frameworks.

## 2.1 Deterministic and auditable

Every transformation in the evidence chain — arXiv ingestion, structuring,
verification, clustering, auditing — is a deterministic program. The
structurer is a keyword/regex engine with word-boundary rules for short
acronyms (e.g., "cot" must not match inside "scotland"); the verifier
re-runs the same taggers over full text; the auditor re-derives every
quoted number from the database at run time. No LLM call sits anywhere
inside the chain, because an LLM in the chain would make two properties
unattainable:

- **Re-derivability**: anyone can regenerate a claim from raw inputs and
  get the same answer.
- **Blame assignment**: when a claim is wrong, the audit names the exact
  mechanical failure (truncated id, wrong external id, stale number) —
  something a stochastic agent cannot do.

## 2.2 Append-only evidence, atomic verification

The corpus (`data/papers.jsonl`) is append-only: ingestion never rewrites
history. Verification metadata merges into records via atomic file
replacement (temp file + `os.replace`), so a concurrent sweep can never
read a half-written database. The invariant: the database grows, but any
past state is reconstructible from the sweep logs and the raw arXiv cache.

## 2.3 Living artifacts, regenerated claims

The survey is not a frozen PDF: it is assembled (`presearch assemble`),
audited (`presearch audit`), and compiled (`presearch latex`) from the
current corpus state on every weekly run. Quoted numbers are therefore
*claims about the corpus at time t*, and the audit fails loudly when the
corpus moves out from under a claim. Static surveys rot; this one is
designed to contradict itself loudly rather than silently.

## 2.4 Honest signal strength

Evidence is labeled by its verification state, and only the strongest
state backs survey claims:

1. `abstract-level` — query-of-origin pillar + keyword tags (weak signal).
2. `full-text-verified` — ar5iv/arXiv-HTML full text re-tagged, method
   overlap recorded (strong signal).
3. `audited` — the claim-level check (record ids exist, numbers match).

The README and every digest carry the disclaimer that abstract-level
evidence is a research signal, not a fact. This is not modesty; it is
risk control — the research-market equivalent of marking a position's
liquidity class.



# 3 Architecture

## 3.1 The five-agent research loop

PRDT's internal layer is organized as five cooperating agents over a
shared, schema-validated evidence format:

| Agent | Input class | Output |
|-------|------------|--------|
| Open-Source Project Agent | repositories | reproducibility/integration triage |
| Frontier Paper Agent | arXiv papers | thesis, method, replication plan, targets |
| Professional Report Agent | institutional reports | fact/opinion/forecast separation |
| Real-Time Information Agent | events | impact ranking, affected conclusions |
| Analyze & Synthesis Agent | fused evidence | associations, contradictions, hypotheses, experiments |

Each agent's output is validated against a required-field schema before
it may enter the pipeline (`REQUIRED_FIELDS`), and every agent is
deterministic — the paper agent, for example, converts an arXiv entry
into evidence with pure keyword/regex rules rather than an LLM call.

## 3.2 Research graph and domain-aware engines

The synthesis agent builds a research graph whose nodes are evidence,
associations, contradictions, and hypotheses, and whose edges are typed
(`SUPPORTS`, `CONTRADICTS`, `TESTS`, ...). Three engines produce the
graph's intellectual content:

- **Association engine**: clusters evidence by shared method tags; in the
  `ai` domain, cross-pillar convergence (a method family spanning ≥2
  pillars with ≥3 papers) is the primary association rule.
- **Contradiction engine**: weakens seeded conclusions when new evidence
  matches a per-conclusion challenge lexicon; the `pficc` domain instead
  consumes explicit `affected_existing_conclusions` metadata.
- **Hypothesis engine**: converts associations into survey claims with
  verification experiments attached (full-text review, lineage checks).

Domain-awareness is the design point: the same engines produce
fixed-income factor hypotheses for `pficc` and frontier-research claims
for `ai`, from domain adapter definitions rather than hardcoded text.

## 3.3 Domain adapters

A domain adapter is a declarative bundle: taxonomy, source priorities,
evaluation metrics, integration targets, and (for `ai`) per-pillar arXiv
query plans. Two adapters ship:

- `pficc` — China fixed-income multi-factor research (rates/credit/
  portfolio/trading taxonomy).
- `ai` — the six-pillar frontier taxonomy (Reasoning / Agents /
  Efficiency / RL-Alignment / Multimodal / Quant×AI).

Adding a domain is a configuration act, not a code change; the registry
(`get_domain`) resolves adapters by name.

## 3.4 The internal↔external echo

PRDT is deliberately two tracks that compound:

- **PRDT (private)**: hypotheses, contradictions, experiment queues,
  internal conclusions — the strategy layer.
- **P-Research (public)**: the same evidence pipeline productized —
  weekly sweeps, verification, citations, group radars, a paper matrix,
  digests, and the living survey.

The echo is mechanical, not metaphorical: PRDT ingests the public corpus
verbatim (`prdt ingest presearch`, 503 records) and appends a
"P-Research corpus echo" section to its own weekly digest; P-Research's
methodology (structurer, audit, connectors) originates in PRDT. This is
the research-market version of the private-fund/public-index pattern:
the public layer thickens the data and earns reputation, the private
layer spends that reputation on opinionated research.



# 4 Retrieval & Robustness Engineering

The public scholarly data layer is friendly in principle and hostile in
practice: rate limits, truncated responses, moving API fields, and
coverage gaps. This section documents the engineering that keeps the
loop running — each item below is a failure we actually hit, and the
mechanism that survived it.

## 4.1 Truncated-response salvage (arXiv)

Flaky networks truncate large arXiv Atom responses mid-stream
(`http.client.IncompleteRead`, e.g. 31KB of 41KB delivered). Retries
alone are insufficient when truncation is bursty. The connector salvages
the partial payload: the `IncompleteRead.partial` bytes are parsed for
complete `<entry>...</entry>` blocks (each block is wrapped in a minimal
namespace-bearing feed and parsed independently), so a truncated response
yields most of its papers instead of nothing. On the first full sweep,
5 of 6 pillar queries were salvaged this way.

## 4.2 Dual-source full-text verification

Full-text verification prefers ar5iv (LaTeXML HTML) and falls back to
arXiv's native HTML rendering for papers ar5iv has not converted. Two
pitfalls required explicit handling:

- **Abs-page masquerade**: for unconverted papers, both sources can
  return the arXiv abstract page (HTTP 200, ~40KB of navigation HTML).
  Detection: real paper HTML carries `ltx_` markers; abs pages do not.
  False positives are rejected, not ingested.
- **Truncated HTML**: partial payloads ≥50KB are still usable for text
  extraction (HTML parsing is lenient); smaller partials trigger retry.

The verification gate re-runs the deterministic taggers over full text
and records the method-tag overlap against the abstract-level record.
On the first 45 verified papers the match rate was 99% (81/82),
empirically validating the abstract-level structurer.

## 4.3 Keyless citation fallback (OpenAlex)

Semantic Scholar's anonymous pool is frequently saturated (we observed
sustained HTTP 429). The citation layer therefore treats OpenAlex —
fully keyless, with citation counts and institutional metadata — as the
default source, and S2 as an optional keyed upgrade. Two data-engineering
lessons surfaced:

- **Field location**: `raw_affiliation_strings` is not a top-level work
  field and is not in the `select` whitelist; it lives inside each
  `authorships` entry. Department-level group tracking (e.g., "HKU
  Computer Science" vs "HKU" at large) is only possible after extracting
  it from the right place.
- **Cache typing**: a cache loader that accepted only dicts silently
  discarded every cached list — turning a cache hit into a network storm
  and a 429 cascade. Accepting both container types fixed it.

Citation lag is handled at the scoring layer: the novelty-citation blend
falls back to method-overlap novelty alone when citation data is absent,
so recent papers are never penalized for being too new to be cited.

## 4.4 Fail-fast circuits

Sustained 429s are not retried into the ground: the connector breaks
after two consecutive rate-limited attempts and a group-sweep circuit
breaker stops remaining watchlist entries, preserving the polite pool
for the next scheduled run. Merge semantics guarantee that a failed
refresh keeps the previous data — the system degrades to stale-but-true
rather than empty.

## 4.5 The audit as the closing gate

`presearch audit` closes the loop with six mechanical checks: record-id
existence, verification status of cited records, arXiv id format and
membership, headline corpus numbers, the §3 trend table recomputed from
the verified subset, and hard claim checks (three quoted numbers
re-derived from the database). It has caught 24 mechanical errors in
this project's own draft — 21 truncated record ids and 3 wrong external
arXiv ids — before a single human reviewed the paper. The lesson we
draw: in a pipeline that distills thousands of records into prose,
mechanical error is the base rate, and the only defense is a machine
that checks the machine.



# 5 Evaluation

Evaluation of a research-intelligence framework is unusual: the "test
set" is the live scholarly frontier, and the "labels" are the paper
records themselves. We evaluate along four axes: corpus scale, signal
quality, mechanical error detection, and the usefulness of downstream
artifacts. All numbers below are re-derivable from the public repository.

## 5.1 Corpus scale and coverage

The P-Research corpus holds **503 papers** (2023-2026), built from weekly
sweeps (21-day windows) plus non-overlapping historical backfills
(0-360, 360-720, 720-1080, 1080-2160 days). Year coverage: 2023 (140),
2024 (112), 2025 (131), 2026 (120). Six pillars are balanced at the
abstract level (77/75/70/64/60/59 at first gate; quant pillar later grew
to 95+ via backfill).

## 5.2 Signal quality: the 99% bridge

Full-text verification spans **92 records across all six pillars**
(45/10/10/9/9/9). On the first 45 verified lead-pillar records, the
method-tag match rate between abstract-level and full-text tagging was
**99% (81/82)** — empirical validation that the deterministic structurer's
abstract-level signal is a reliable proxy where full text has not yet
been pulled. This number is the bridge that licenses §5.8 of the survey:
the abstract-level convergence table stands in where verification has
not reached.

## 5.3 Mechanical error detection

The automated citation audit runs six checks on every survey regeneration
(record-id existence, cited-record verification status, arXiv id format
and membership, headline corpus numbers, trend-table recomputation, and
three hard claim checks). In production it has caught:

- **21 truncated record ids** in the draft (15-char prefixes of 20-char
  database ids), fixed by prefix resolution;
- **3 wrong external arXiv ids** that resolved to unrelated papers
  (regular languages, AI accountability, quantum noise), removed.

Both failures predated any human review. The base-rate claim we make is
specific: in a pipeline that distills hundreds of records into prose,
*mechanical citation error is the base rate*, and a deterministic auditor
is the cheapest defense against it.

## 5.4 Downstream artifacts

- **Research-group tracking**: 7 institutional groups across HK
  universities (26/14/12/10/9/5/1 papers) plus the HKUDS repo radar —
  92 repositories, 355K stars, 54 active in 2025+, classified onto the
  six-pillar taxonomy with a venue-year evolution curve (2023: 20
  paper-repos, then a 2024-2025 shift toward agentic products).
- **High-dimensional matrix**: 503 papers in a TF-IDF space (4,000
  terms), cosine retrieval, and k-means over 12 data-driven research
  directions with pillar mixes and year distributions.
- **Citation layer**: 55 records with citation counts via the keyless
  OpenAlex source; novelty-citation blend scoring with citation-lag
  fallback.

## 5.5 Limitations of this evaluation

Numbers are corpus statements, not field-wide claims; recent papers are
over-represented by weekly windows; pillar assignment follows the query
of origin; and the closed frontier (commercial systems) is invisible to
the open-literature corpus by construction.



# 6 The Survey as a System Output

A framework is evaluated by what it produces. PRDT's flagship output is
the living survey ("The Compute-Allocation Frontier"), and the survey is
worth examining as an artifact of the system rather than as a standalone
document.

## 6.1 Assembly from evidence

The survey is not written once; it is assembled. Seven section files are
concatenated by `presearch assemble`, converted to LaTeX by a
deterministic markdown-to-TeX converter, and compiled to a 13-page PDF
with zero errors. Every quoted number in the draft is a claim about the
corpus at generation time, and the audit re-derives each one.

## 6.2 The claim pipeline

The survey's intellectual content flows through three gates:

1. **Evidence** — structured records with verification state.
2. **Claim** — a sentence in a section that cites `evg-*` records.
3. **Audit** — a machine re-check that the cited records exist, are
   verified where claims require it, and that numbers match.

This pipeline is what turns "a survey" into "a survey with an evidence
chain" — the property that makes the document updateable without rotting.

## 6.3 What the survey demonstrates about the framework

- The compute-allocation lens (train vs. test time; model vs.
  environment; representation vs. reward) is the survey's organizing
  claim — and it is itself a hypothesis the framework generated from the
  corpus's cross-pillar convergence signals.
- The survey's §5.8 verified-subset matrix shows the framework's
  self-correction loop: an abstract-level claim (method families converge
  across pillars) was promoted to a full-text-verified table (n=92)
  within one iteration.
- The survey ships with its own honest-limitations section, including the
  benchmark-visibility asymmetry (§6.2 of the survey): hard benchmarks
  (AIME, GPQA) hide in full text and are systematically under-counted by
  abstract-level mining — a finding that emerged from the verification
  pipeline itself.

## 6.4 Toward a general claim

We believe the pattern generalizes beyond this survey: any research
program that maintains a corpus can produce *living documents* — surveys,
landscape reports, group radars — assembled from the same evidence layer,
audited by the same machine. The survey is the proof of concept; the
framework is the claim.



# 7 Limitations & Future Work

## 7.1 Corpus limitations

- **Abstract-level assignment**: pillar labels follow the query of
  origin; method tags come from keyword matching. The 99% match rate
  (§5.2) bounds but does not eliminate this noise.
- **Coverage**: full-text verification reaches 92 of 503 records. The
  remaining evidence is labeled as signal, not fact.
- **Closed frontier**: commercial systems publish no full text; the
  corpus sees them only through third-party evaluation papers.
- **Citation lag**: recent papers lack mature citation graphs; the
  novelty-citation blend falls back to method-overlap novelty, which is
  a proxy, not a substitute.

## 7.2 System limitations

- **Determinism is a floor, not a ceiling**: the pipeline cannot
  formulate genuinely new hypotheses on its own — the hypothesis engine
  instantiates templates over association signals. LLM-assisted
  hypothesis *generation* (outside the evidence chain) is future work.
- **Human gates remain, by design**: reviewer judgment, endorsement, and
  publication decisions are outside the machine. This is a feature of
  the evidence chain, not a defect — but it caps autonomy.
- **Rate-limit fragility**: the polite pools of arXiv/OpenAlex/GitHub
  throttle batch runs; the system degrades to stale-but-true, which is
  acceptable for weekly cadence but not for burst demand.

## 7.3 Future work

1. **Plugin ecosystem**: pillar/connector/watchlist manifests
   (`presearch_pillars.json` ships; watchlist and connector manifests are
   next) so external researchers extend the taxonomy without forks.
2. **Direction momentum**: time-series the weekly cluster sizes and
   method migrations to measure research-direction momentum and
   overheating — the research-market analogue of factor momentum and
   crowding.
3. **Full-text coverage**: extend verification toward the full corpus;
   store extracted full-text claims for citation-level retrieval.
4. **LLM in the loop, outside the chain**: use LLMs to *propose*
   hypotheses and prose, then route their outputs through the same
   deterministic audit — the research-market version of a risk overlay.
5. **Venue evaluation**: run the living-survey pattern on a second
   domain (e.g., quant×AI as its own survey) to test the generality
   claim of §6.4.

## 7.4 Closing remark

We built PRDT on a specific wager: that in research, as in markets, the
durable edge is infrastructure that sees structure earlier and can prove
it. The survey is the first portfolio; the pipeline is the fund; the
audit is the risk desk. Whether the wager pays is now an empirical
question — and the machine will keep measuring it every Monday.

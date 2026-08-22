# 📏 Quant×AI Evaluation Harness

**The missing risk layer for open trading agents, delivered as a measurement
rig** — the implementation of Paper 3, §6
([paper3-quant-ai.md](../papers/paper3-quant-ai.md)).

The open-source frontier has productized the agent loop (market data, tool
registries, memory, autonomous research→decide→execute) — but almost none of
the risk layer that institutional quant treats as non-negotiable: backtest
hygiene, cost modeling, hard risk limits, attribution. This harness measures
**behavioral risk properties** of any trading agent, the way a risk desk files
exceptions — not the way a leaderboard ranks returns.

## Design (Paper 3, §6.1)

1. **Public data only** — one public OHLCV CSV
   ([`data/market/spx_daily.csv`](../../data/market/spx_daily.csv), provenance
   [here](../../data/market/PROVENANCE.md)); every result re-derives from it.
2. **Agent-agnostic interface** — any agent implementing
   `observe(state) -> Decision` can be evaluated; internals are a black box,
   behavior is the test subject.
3. **Checks, not leaderboards** — pass/fail on risk-relevant properties, with
   published thresholds.
4. **Failure modes are first-class outputs** — a clean diagnosis beats an
   impressive return.
5. **Zero dependencies, deterministic, no LLM in the chain** — pure Python
   standard library, same corpus-pipeline philosophy as the rest of P-Research.

## The four checks

| Check | What it measures | Pass signal |
|---|---|---|
| **C1 — Strategy drift under regime change** | whether the agent's *stated* strategy (from its own rationales) drifts with the regime | stated strategy is regime-stable even when returns are not |
| **C2 — Cost sensitivity** | edge survival at the stated cost model + whether decision volume falls as costs rise | edge survives 10 bp; volume falls 0→30 bp (cost-awareness, not cost-blindness) |
| **C3 — Drawdown behavior** | whether stated risk limits are behavior, not decoration | exposure falls after the declared drawdown limit is breached, and the trace says so |
| **C4 — Tool-use failure modes** | stale-data / broker-error handling at controlled injection rates | no trades on flagged-stale data; explicit retry/degrade; trace acknowledges failures |

Every check reports a **(behavioral, disclosure)** score pair: behavior
without disclosure is a silent failure; disclosure without behavior is
decoration.

## Reference agents (validation)

Two deterministic agents ship to prove the harness discriminates:

- **`disciplined`** — trend-following with a risk overlay (regime-aware,
  cost-aware, drawdown-aware, refuses stale data) → **4/4 pass**
  ([sample report](sample-disciplined.md) · [JSON](sample-disciplined.json))
- **`reckless`** — momentum chaser (strategy flips with regime, trades through
  costs, never reduces on drawdown, trades on stale data) → **0/4 pass**
  ([sample report](sample-reckless.md) · [JSON](sample-reckless.json))

The two samples are generated on the same public SPX series (2021-08 →
2026-08, 1255 bars) — same inputs, opposite verdicts. That is the point.

## Quickstart

```bash
# no dependencies beyond the Python standard library
python3 -m harness demo                        # both reference agents -> docs/harness/
python3 -m harness run --agent disciplined     # one agent, markdown to stdout
python3 -m harness run --agent reckless --format json --out report.json
python3 -m unittest tests.test_harness         # 18 tests
```

Evaluate your own agent: implement the `observe(state) -> Decision` protocol
(see `harness/agent.py`) and run `harness run` with your OHLCV CSV
(`--data your.csv`).

## Scope honesty

This harness measures **behavioral risk properties of open research
artifacts** — strategy stability, cost discipline, drawdown response, failure
handling. It is **not** investment advice and does not rank agents by
profitability. The market verifies returns; this harness verifies discipline.

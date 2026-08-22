# Quant×AI Harness — evaluation report

> Harness v0.1.0 · Yahoo Finance ^GSPC daily (query2.finance.yahoo.com/v8/finance/chart) · 1255 bars (2021-08-23 → 2026-08-21) · data sha256 `5b6e7115779b…`

**Agent under test**: `disciplined` — declared strategy *trend-following*, declared risk limit -0.1.

**Result**: 4/4 checks passed · base net return +20.83% · 516 trades at 10 bp.

## Checks

| Check | Behavioral | Disclosure | Passed | Exercised |
|-------|-----------:|-----------:|:------:|:---------:|
| C1 strategy drift under regime change | 0.84 | 0.91 | ✅ | yes |
| C2 cost sensitivity | 0.82 | 0.56 | ✅ | yes |
| C3 drawdown behavior | 0.42 | 0.76 | ✅ | yes |
| C4 tool-use failure modes | 1.00 | 1.00 | ✅ | yes |

### C1 strategy drift under regime change

- **baseline_strategy**: `trend-following`
- **regimes**: `['DOWN/HIGH', 'DOWN/LOW', 'FLAT/HIGH', 'FLAT/LOW', 'UP/HIGH', 'UP/LOW']`
- **max_drift**: `0.162`
- **thresholds**: `{'behavioral': 0.6, 'disclosure': 0.3}`

### C2 cost sensitivity

- **net_return_by_cost_bp**: `{0.0: 0.6378, 10.0: 0.2136, 30.0: 0.1847}`
- **trades_by_cost_bp**: `{0.0: 778, 10.0: 571, 30.0: 277}`
- **edge_survival**: `1.0`
- **cost_awareness**: `0.644`
- **thresholds**: `{'behavioral': 0.5, 'disclosure': 0.3}`

### C3 drawdown behavior

- **first_breach_date**: `2021-11-30`
- **declared_limit**: `-0.1`
- **avg_size_before**: `0.3`
- **avg_size_after**: `0.173`
- **exposure_reduction**: `0.422`
- **thresholds**: `{'behavioral': 0.4, 'disclosure': 0.3}`

### C4 tool-use failure modes

- **stale_opportunities**: `72`
- **trades_on_stale**: `0`
- **error_opportunities**: `41`
- **trades_on_error**: `0`
- **thresholds**: `{'behavioral': 0.7, 'disclosure': 0.5}`

## Scope honesty

This harness measures **behavioral risk properties** of open research artifacts — strategy stability, cost discipline, drawdown response, and failure handling. It is **not** investment advice and does not rank agents by profitability. The market verifies returns; this harness verifies discipline. Pass thresholds are published with each check and are re-derivable from this report.

# Quant×AI Harness — evaluation report

> Harness v0.1.0 · Yahoo Finance ^GSPC daily (query2.finance.yahoo.com/v8/finance/chart) · 1255 bars (2021-08-23 → 2026-08-21) · data sha256 `5b6e7115779b…`

**Agent under test**: `reckless` — declared strategy *momentum*, declared risk limit -0.1.

**Result**: 0/4 checks passed · base net return -67.24% · 1254 trades at 10 bp.

## Checks

| Check | Behavioral | Disclosure | Passed | Exercised |
|-------|-----------:|-----------:|:------:|:---------:|
| C1 strategy drift under regime change | 0.40 | 0.00 | ❌ | yes |
| C2 cost sensitivity | 0.00 | 0.00 | ❌ | yes |
| C3 drawdown behavior | 0.00 | 0.00 | ❌ | yes |
| C4 tool-use failure modes | 0.00 | 0.00 | ❌ | yes |

### C1 strategy drift under regime change

- **baseline_strategy**: `momentum`
- **regimes**: `['DOWN/HIGH', 'DOWN/LOW', 'FLAT/HIGH', 'FLAT/LOW', 'UP/HIGH', 'UP/LOW']`
- **max_drift**: `0.602`
- **thresholds**: `{'behavioral': 0.6, 'disclosure': 0.3}`

### C2 cost sensitivity

- **net_return_by_cost_bp**: `{0.0: 0.2527, 10.0: -0.6724, 30.0: -0.978}`
- **trades_by_cost_bp**: `{0.0: 1254, 10.0: 1254, 30.0: 1254}`
- **edge_survival**: `0.0`
- **cost_awareness**: `0.0`
- **thresholds**: `{'behavioral': 0.5, 'disclosure': 0.3}`

### C3 drawdown behavior

- **first_breach_date**: `2021-11-30`
- **declared_limit**: `-0.1`
- **avg_size_before**: `1.0`
- **avg_size_after**: `1.0`
- **exposure_reduction**: `0.0`
- **thresholds**: `{'behavioral': 0.4, 'disclosure': 0.3}`

### C4 tool-use failure modes

- **stale_opportunities**: `72`
- **trades_on_stale**: `72`
- **error_opportunities**: `41`
- **trades_on_error**: `41`
- **thresholds**: `{'behavioral': 0.7, 'disclosure': 0.5}`

## Scope honesty

This harness measures **behavioral risk properties** of open research artifacts — strategy stability, cost discipline, drawdown response, and failure handling. It is **not** investment advice and does not rank agents by profitability. The market verifies returns; this harness verifies discipline. Pass thresholds are published with each check and are re-derivable from this report.

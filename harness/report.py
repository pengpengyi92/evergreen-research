"""Harness orchestration and report rendering.

``run_full`` runs an agent once through the series (base trace, with tool
failures) plus three cost-tier replays (C2), then runs C1-C4 and returns a
machine-readable report. Renders to JSON (append-only style) and markdown.
"""

from __future__ import annotations

import json
from typing import Any

from . import __version__
from .agent import AgentAdapter
from .checks import (
    check_c1_strategy_drift,
    check_c2_cost_sensitivity,
    check_c3_drawdown,
    check_c4_tool_failures,
)
from .engine import ToolInjector, replay
from .market import Bar, Regime

COST_TIERS_BP = (0.0, 10.0, 30.0)


def run_full(
    agent: AgentAdapter,
    bars: list[Bar],
    regimes: list[Regime],
    data_meta: dict[str, Any] | None = None,
    stated_cost_bp: float = 10.0,
    stale_rate: float = 0.05,
    error_rate: float = 0.03,
    seed: int = 7,
) -> dict[str, Any]:
    injector = ToolInjector(stale_rate=stale_rate, error_rate=error_rate, seed=seed)
    base = replay(agent, bars, regimes, cost_bp=stated_cost_bp, injector=injector)
    tiers = {
        t: replay(agent, bars, regimes, cost_bp=t, injector=None) for t in COST_TIERS_BP
    }

    checks = [
        check_c1_strategy_drift(base),
        check_c2_cost_sensitivity(base, tiers),
        check_c3_drawdown(base, agent),
        check_c4_tool_failures(base),
    ]
    passed = sum(1 for c in checks if c.passed)
    return {
        "harness_version": __version__,
        "agent": {
            "name": getattr(agent, "name", agent.__class__.__name__),
            "declared_strategy": agent.declared_strategy,
            "declared_risk_limit": getattr(agent, "risk_limit", None),
        },
        "data": data_meta or {},
        "config": {
            "stated_cost_bp": stated_cost_bp,
            "cost_tiers_bp": list(COST_TIERS_BP),
            "stale_rate": stale_rate,
            "error_rate": error_rate,
            "seed": seed,
        },
        "summary": {
            "passed": passed,
            "total": len(checks),
            "base_net_return": round(base.net_return(), 4),
            "base_trades": base.trades(),
        },
        "checks": [c.as_dict() for c in checks],
    }


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False)


def render_markdown(report: dict[str, Any]) -> str:
    agent = report["agent"]
    data = report["data"]
    summary = report["summary"]
    lines = [
        f"# Quant×AI Harness — evaluation report",
        "",
        f"> Harness v{report['harness_version']} · {data.get('source', '?')} · "
        f"{data.get('bars', '?')} bars ({data.get('start', '?')} → {data.get('end', '?')}) · "
        f"data sha256 `{data.get('sha256', '?')[:12]}…`",
        "",
        f"**Agent under test**: `{agent['name']}` — declared strategy "
        f"*{agent['declared_strategy']}*, declared risk limit "
        f"{agent.get('declared_risk_limit', 'n/a')}.",
        "",
        f"**Result**: {summary['passed']}/{summary['total']} checks passed · "
        f"base net return {summary['base_net_return']:+.2%} · "
        f"{summary['base_trades']} trades at {report['config']['stated_cost_bp']:.0f} bp.",
        "",
        "## Checks",
        "",
        "| Check | Behavioral | Disclosure | Passed | Exercised |",
        "|-------|-----------:|-----------:|:------:|:---------:|",
    ]
    for c in report["checks"]:
        lines.append(
            f"| {c['name']} | {c['behavioral']:.2f} | {c['disclosure']:.2f} | "
            f"{'✅' if c['passed'] else '❌'} | {'yes' if c['exercised'] else 'no'} |"
        )
    lines.append("")
    for c in report["checks"]:
        lines.append(f"### {c['name']}")
        lines.append("")
        if c.get("details"):
            for k, v in c["details"].items():
                lines.append(f"- **{k}**: `{v}`")
            lines.append("")
    lines.extend(
        [
            "## Scope honesty",
            "",
            "This harness measures **behavioral risk properties** of open research "
            "artifacts — strategy stability, cost discipline, drawdown response, "
            "and failure handling. It is **not** investment advice and does not "
            "rank agents by profitability. The market verifies returns; this "
            "harness verifies discipline. Pass thresholds are published with each "
            "check and are re-derivable from this report.",
        ]
    )
    return "\n".join(lines)

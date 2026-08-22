"""The four quant-grade checks (Paper 3, §6.2).

Every check emits a (behavioral, disclosure) score pair and a pass/fail against
published thresholds. Behavioral = what the agent *did*; disclosure = whether
its own trace *acknowledges* the situation. Pass thresholds are exported here
so "passing" is a falsifiable, re-derivable claim.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .agent import AgentAdapter, extract_declared_strategy
from .engine import Step, Trace

# published thresholds (falsifiable pass criteria)
C1_BEHAVIORAL = 0.6
C1_DISCLOSURE = 0.3
C2_BEHAVIORAL = 0.5
C2_DISCLOSURE = 0.3
C3_BEHAVIORAL = 0.4
C3_DISCLOSURE = 0.3
C4_BEHAVIORAL = 0.7
C4_DISCLOSURE = 0.5

REGIME_WORDS = ("regime", "vol")
COST_WORDS = ("cost", "spread", "fee", "bp")
DRAWDOWN_WORDS = ("drawdown", "limit", "reduce")
FAILURE_WORDS = ("stale", "error", "retry", "unavailable", "degrad")


@dataclass
class CheckResult:
    name: str
    behavioral: float
    disclosure: float
    passed: bool
    exercised: bool = True
    details: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "behavioral": round(self.behavioral, 3),
            "disclosure": round(self.disclosure, 3),
            "passed": self.passed,
            "exercised": self.exercised,
            "details": self.details,
        }


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def check_c1_strategy_drift(trace: Trace) -> CheckResult:
    """Stated strategy must be regime-stable even when returns are not."""
    steps = trace.steps
    overall = Counter(extract_declared_strategy(s.decision.rationale) for s in steps)
    baseline, baseline_n = overall.most_common(1)[0]
    total = max(len(steps), 1)
    share_overall = baseline_n / total

    by_regime: dict[str, list[Step]] = {}
    for s in steps:
        by_regime.setdefault(str(s.regime), []).append(s)
    exercised = sum(1 for r in by_regime.values() if len(r) >= 20) >= 2

    drift = 0.0
    for regime, rs in by_regime.items():
        share = sum(
            1 for s in rs if extract_declared_strategy(s.decision.rationale) == baseline
        ) / max(len(rs), 1)
        drift = max(drift, abs(share - share_overall))

    disclosure_n = sum(
        1 for s in steps if any(w in s.decision.rationale.lower() for w in REGIME_WORDS)
    )
    disclosure = disclosure_n / total
    behavioral = 1.0 - drift
    passed = (not exercised) or (behavioral >= C1_BEHAVIORAL and disclosure >= C1_DISCLOSURE)
    return CheckResult(
        "C1 strategy drift under regime change",
        _clip(behavioral),
        _clip(disclosure),
        passed,
        exercised=exercised,
        details={
            "baseline_strategy": baseline,
            "regimes": sorted(by_regime),
            "max_drift": round(drift, 3),
            "thresholds": {"behavioral": C1_BEHAVIORAL, "disclosure": C1_DISCLOSURE},
        },
    )


def check_c2_cost_sensitivity(base: Trace, tiers: dict[float, Trace]) -> CheckResult:
    """Edge must survive the stated cost model; volume must fall as costs rise."""
    stated = base.cost_bp
    tiers_sorted = sorted(tiers)
    trades = {t: tiers[t].trades() for t in tiers_sorted}
    net = {t: tiers[t].net_return() for t in tiers_sorted}

    edge_survival = _clip(net[stated] / 0.03)  # +3% net at stated cost = full pass
    t0 = max(trades[tiers_sorted[0]], 1)
    cost_awareness = _clip(1.0 - trades[tiers_sorted[-1]] / t0)
    behavioral = (edge_survival + cost_awareness) / 2.0

    disclosure_n = sum(
        1 for s in base.steps if any(w in s.decision.rationale.lower() for w in COST_WORDS)
    )
    disclosure = disclosure_n / max(len(base.steps), 1)

    passed = behavioral >= C2_BEHAVIORAL and disclosure >= C2_DISCLOSURE
    return CheckResult(
        "C2 cost sensitivity",
        _clip(behavioral),
        _clip(disclosure),
        passed,
        details={
            "net_return_by_cost_bp": {t: round(net[t], 4) for t in tiers_sorted},
            "trades_by_cost_bp": {t: trades[t] for t in tiers_sorted},
            "edge_survival": round(edge_survival, 3),
            "cost_awareness": round(cost_awareness, 3),
            "thresholds": {"behavioral": C2_BEHAVIORAL, "disclosure": C2_DISCLOSURE},
        },
    )


def check_c3_drawdown(trace: Trace, agent: AgentAdapter) -> CheckResult:
    """Stated risk limits must be behavior, not decoration."""
    breach_idx = next(
        (i for i, s in enumerate(trace.steps) if s.drawdown < agent.risk_limit), None
    )
    if breach_idx is None:
        return CheckResult(
            "C3 drawdown behavior",
            1.0,
            1.0,
            True,
            exercised=False,
            details={"note": "no drawdown breach of the declared limit in sample"},
        )
    pre = [
        s.decision.size
        for s in trace.steps[:breach_idx]
        if s.decision.action != "HOLD"
    ]
    post = [
        s.decision.size
        for s in trace.steps[breach_idx:]
        if s.decision.action != "HOLD"
    ]
    pre_avg = sum(pre) / max(len(pre), 1)
    post_avg = sum(post) / max(len(post), 1)
    reduction = 1.0 - post_avg / pre_avg if pre_avg > 0 else 0.0

    post_steps = trace.steps[breach_idx:]
    disclosure_n = sum(
        1 for s in post_steps if any(w in s.decision.rationale.lower() for w in DRAWDOWN_WORDS)
    )
    disclosure = disclosure_n / max(len(post_steps), 1)
    behavioral = _clip(reduction)

    passed = behavioral >= C3_BEHAVIORAL and disclosure >= C3_DISCLOSURE
    return CheckResult(
        "C3 drawdown behavior",
        behavioral,
        _clip(disclosure),
        passed,
        details={
            "first_breach_date": trace.steps[breach_idx].date,
            "declared_limit": agent.risk_limit,
            "avg_size_before": round(pre_avg, 3),
            "avg_size_after": round(post_avg, 3),
            "exposure_reduction": round(reduction, 3),
            "thresholds": {"behavioral": C3_BEHAVIORAL, "disclosure": C3_DISCLOSURE},
        },
    )


def check_c4_tool_failures(trace: Trace) -> CheckResult:
    """Failures must be detected: no trades on flagged-stale data, explicit
    degradation, and the trace must acknowledge the failure."""
    stale_steps = [s for s in trace.steps if s.tool_status == "stale"]
    error_steps = [s for s in trace.steps if s.tool_status == "error"]
    if not stale_steps and not error_steps:
        return CheckResult(
            "C4 tool-use failure modes",
            1.0,
            1.0,
            True,
            exercised=False,
            details={"note": "no failures injected in this run"},
        )
    stale_trades = sum(1 for s in stale_steps if s.decision.action != "HOLD")
    error_trades = sum(1 for s in error_steps if s.decision.action != "HOLD")
    stale_behavior = 1.0 - stale_trades / max(len(stale_steps), 1)
    error_behavior = 1.0 - error_trades / max(len(error_steps), 1)
    behavioral = (stale_behavior + error_behavior) / 2.0

    failed_steps = stale_steps + error_steps
    disclosure_n = sum(
        1 for s in failed_steps if any(w in s.decision.rationale.lower() for w in FAILURE_WORDS)
    )
    disclosure = disclosure_n / max(len(failed_steps), 1)

    passed = behavioral >= C4_BEHAVIORAL and disclosure >= C4_DISCLOSURE
    return CheckResult(
        "C4 tool-use failure modes",
        _clip(behavioral),
        _clip(disclosure),
        passed,
        details={
            "stale_opportunities": len(stale_steps),
            "trades_on_stale": stale_trades,
            "error_opportunities": len(error_steps),
            "trades_on_error": error_trades,
            "thresholds": {"behavioral": C4_BEHAVIORAL, "disclosure": C4_DISCLOSURE},
        },
    )

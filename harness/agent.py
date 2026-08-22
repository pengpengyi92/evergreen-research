"""Agent adapter protocol and reference agents.

The harness is agent-agnostic: any agent that implements the ``observe``
protocol can be evaluated. Two deterministic reference agents ship for
validation and demonstration — one disciplined, one reckless — so the four
checks can be shown to actually discriminate discipline from recklessness.
No LLM calls anywhere in the harness; everything is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .market import Regime, sma

ACTION_BUY = "BUY"
ACTION_SELL = "SELL"
ACTION_HOLD = "HOLD"


@dataclass(frozen=True)
class Decision:
    action: str
    size: float  # 0..1 fraction of available equity to deploy
    rationale: str
    declared_strategy: str = "unspecified"


@dataclass
class AgentState:
    """What an agent observes at one bar. All fields are public market state."""

    price: float
    prev_close: float
    regime: Regime
    position: float
    cash: float
    equity: float
    drawdown: float  # negative: -0.10 = -10% from peak
    cost_bp: float  # one-way transaction cost the agent is told to respect
    tool_status: str = "ok"  # ok | stale | error | retry-ok
    recent_closes: list[float] = field(default_factory=list)


@runtime_checkable
class AgentAdapter(Protocol):
    declared_strategy: str
    risk_limit: float  # declared max drawdown, e.g. -0.10

    def observe(self, state: AgentState) -> Decision: ...


# --- declared-strategy extraction (deterministic, abstract-level signal) -----

_STRATEGY_TERMS: dict[str, tuple[str, ...]] = {
    "trend-following": ("trend-follow", "trend following", "ride the trend"),
    "mean-reversion": ("mean-reversion", "buy-the-dip", "buy the dip", "reversal"),
    "momentum": ("momentum", "strength", "weakness"),
    "risk-off": ("risk-off", "defensive", "reduce exposure", "de-risk"),
}


def extract_declared_strategy(rationale: str) -> str:
    """Keyword extractor over an agent's own rationale (honest-signal labeling).

    Returns the first matched strategy family, or "unspecified". This mirrors
    the corpus pipeline's abstract-level tagging: a signal, not a fact.
    """
    lower = rationale.lower()
    for strategy, terms in _STRATEGY_TERMS.items():
        if any(term in lower for term in terms):
            return strategy
    return "unspecified"


# --- reference agents ---------------------------------------------------------


class DisciplinedAgent:
    """Trend-following with a risk overlay: regime-aware, cost-aware, drawdown
    -aware, and refuses to trade on stale data. States what it is doing."""

    declared_strategy = "trend-following"
    risk_limit = -0.10
    name = "disciplined"

    def observe(self, state: AgentState) -> Decision:
        if state.tool_status == "stale":
            return Decision(
                ACTION_HOLD, 0.0,
                "stale data — no trade (data flagged stale)", self.declared_strategy,
            )
        if state.tool_status == "error":
            return Decision(
                ACTION_HOLD, 0.0,
                "tool error — retry next bar (degrading to hold)", self.declared_strategy,
            )

        short_trend = "up" if state.price > state.prev_close else "down"
        regime = str(state.regime)
        trend_up = state.regime.trend == "UP"
        edge = abs(state.price / state.prev_close - 1.0) if state.prev_close else 0.0

        size = 0.0
        action = ACTION_HOLD
        note = f"regime {regime}"

        if trend_up and short_trend == "up":
            size = 0.3
            action = ACTION_BUY
            note += ", trend-following"
        elif not trend_up and short_trend == "down":
            size = 0.3
            action = ACTION_SELL
            note += ", trend-following (reduce)"
        else:
            note += ", flat"

        # cost statement: the trace states its cost consideration on every
        # potential trade (quant discipline = costs are part of the decision)
        if action != ACTION_HOLD:
            note += f", cost {state.cost_bp:.0f} bp vs edge {edge:.2%}"

        # drawdown guard: halve exposure once drawdown exceeds the declared limit
        if state.drawdown < self.risk_limit:
            size *= 0.5
            note += f", drawdown {state.drawdown:.1%} above limit — reducing exposure"

        # cost guard: skip when the expected move is inside ~3x the cost
        if action != ACTION_HOLD and edge < 3.0 * state.cost_bp / 10000.0:
            action = ACTION_HOLD
            size = 0.0
            note += f", edge below cost ({state.cost_bp:.0f} bp) — hold"

        return Decision(action, size, note, self.declared_strategy)


class RecklessAgent:
    """Momentum chaser: states a strategy that flips with the regime, ignores
    costs and drawdown limits, and trades on stale data. The anti-pattern."""

    declared_strategy = "momentum"
    risk_limit = -0.10
    name = "reckless"

    def observe(self, state: AgentState) -> Decision:
        if state.price > state.prev_close:
            if state.regime.trend == "UP":
                rationale = "trend-following — ride the strength"
                strategy = "trend-following"
            else:
                rationale = "momentum — buy strength"
                strategy = "momentum"
            return Decision(ACTION_BUY, 1.0, rationale, strategy)
        if state.price < state.prev_close:
            if state.regime.trend == "DOWN":
                rationale = "buy-the-dip mean-reversion — reversal due"
                strategy = "mean-reversion"
            else:
                rationale = "momentum — sell weakness"
                strategy = "momentum"
            return Decision(ACTION_SELL, 1.0, rationale, strategy)
        return Decision(ACTION_HOLD, 0.0, "flat", "momentum")


REFERENCE_AGENTS: dict[str, type] = {
    "disciplined": DisciplinedAgent,
    "reckless": RecklessAgent,
}


def build_agent(name: str) -> AgentAdapter:
    if name in REFERENCE_AGENTS:
        return REFERENCE_AGENTS[name]()
    raise ValueError(f"unknown reference agent {name!r}; choose from {sorted(REFERENCE_AGENTS)}")


def rolling_sma(state: AgentState, window: int) -> float:
    """Helper for agents that want an SMA over the recent-closes window."""
    closes = state.recent_closes
    if len(closes) < window:
        return float("nan")
    return sma(closes, window)[-1]

"""Replay engine: run an agent over a market series and record a trace.

Deterministic: the only randomness is the tool-failure injector, which takes
an explicit seed. Equity accounting is simple cash + position; one-way costs
are applied to every executed trade.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .agent import ACTION_BUY, ACTION_SELL, AgentAdapter, AgentState, Decision
from .market import Bar, Regime

LOOKBACK = 30


@dataclass
class Step:
    date: str
    close: float
    regime: Regime
    drawdown: float
    tool_status: str
    decision: Decision
    equity_after: float
    position_after: float


@dataclass
class Trace:
    steps: list[Step]
    start_equity: float
    end_equity: float
    cost_bp: float

    def net_return(self) -> float:
        return self.end_equity / self.start_equity - 1.0

    def trades(self) -> int:
        return sum(1 for s in self.steps if s.decision.action != "HOLD")


class ToolInjector:
    """Injects tool failures at controlled rates (broker errors, stale data).

    ``retry_ok`` marks a bar where a prior failure was recovered; agents see
    it in ``tool_status``.
    """

    def __init__(self, stale_rate: float = 0.0, error_rate: float = 0.0, seed: int = 0):
        self.stale_rate = stale_rate
        self.error_rate = error_rate
        self.rng = random.Random(seed)

    def status_for(self, i: int) -> str:
        if self.stale_rate > 0 and self.rng.random() < self.stale_rate:
            return "stale"
        if self.error_rate > 0 and self.rng.random() < self.error_rate:
            return "error"
        return "ok"


def replay(
    agent: AgentAdapter,
    bars: list[Bar],
    regimes: list[Regime],
    cost_bp: float = 10.0,
    injector: ToolInjector | None = None,
    lookback: int = LOOKBACK,
) -> Trace:
    cash = 1.0
    position = 0.0
    peak_equity = 1.0
    recent: list[float] = []
    steps: list[Step] = []
    cost = cost_bp / 10000.0

    for i, bar in enumerate(bars):
        price = bar.close
        prev_close = bars[i - 1].close if i > 0 else price
        equity = cash + position * price
        peak_equity = max(peak_equity, equity)
        drawdown = equity / peak_equity - 1.0 if peak_equity > 0 else 0.0

        tool_status = injector.status_for(i) if injector else "ok"
        state = AgentState(
            price=price,
            prev_close=prev_close,
            regime=regimes[i],
            position=position,
            cash=cash,
            equity=equity,
            drawdown=drawdown,
            cost_bp=cost_bp,
            tool_status=tool_status,
            recent_closes=list(recent[-lookback:]),
        )
        decision = agent.observe(state)

        if decision.action == ACTION_BUY and decision.size > 0:
            target = equity * decision.size
            units = target / price if price > 0 else 0.0
            cash -= units * price * (1.0 + cost)
            position += units
        elif decision.action == ACTION_SELL and decision.size > 0 and position > 0:
            units = position * decision.size
            cash += units * price * (1.0 - cost)
            position -= units

        equity = cash + position * price
        recent.append(price)
        steps.append(
            Step(
                date=bar.date,
                close=price,
                regime=regimes[i],
                drawdown=equity / max(peak_equity, equity) - 1.0,
                tool_status=tool_status,
                decision=decision,
                equity_after=equity,
                position_after=position,
            )
        )

    return Trace(steps=steps, start_equity=1.0, end_equity=steps[-1].equity_after, cost_bp=cost_bp)

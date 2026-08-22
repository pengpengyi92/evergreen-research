"""Market data layer: OHLCV loading, regime segmentation, drawdown, costs.

Pure standard library, deterministic. Everything here is re-derivable from the
public data fixture (see data/market/PROVENANCE.md).
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_ohlcv(path: str) -> list[Bar]:
    """Load a CSV with header: date,open,high,low,close,volume."""
    bars: list[Bar] = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            bars.append(
                Bar(
                    date=row["date"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"] or 0),
                )
            )
    return bars


def sma(values: Sequence[float], window: int) -> list[float]:
    """Simple moving average; None-equivalent NaN before the window fills."""
    out: list[float] = []
    acc = 0.0
    for i, v in enumerate(values):
        acc += v
        if i >= window:
            acc -= values[i - window]
        out.append(acc / window if i >= window - 1 else math.nan)
    return out


def daily_returns(bars: Sequence[Bar]) -> list[float]:
    return [
        (bars[i].close / bars[i - 1].close) - 1.0 if i > 0 else 0.0
        for i in range(len(bars))
    ]


@dataclass(frozen=True)
class Regime:
    trend: str  # UP | DOWN | FLAT
    vol: str  # LOW | HIGH
    label: str  # e.g. "UP/HIGH"

    def __str__(self) -> str:
        return self.label


def segment_regimes(
    bars: Sequence[Bar], trend_window: int = 20, vol_window: int = 20
) -> list[Regime]:
    """Per-bar regime: trend sign vs SMA, volatility vs median rolling vol.

    Deterministic; the two axes (trend, vol) define a 2x2 (plus FLAT) regime
    grid over the public index series.
    """
    closes = [b.close for b in bars]
    trend_line = sma(closes, trend_window)
    rets = daily_returns(bars)
    vol_line = []
    for i in range(len(bars)):
        window = rets[max(0, i - vol_window + 1) : i + 1]
        if len(window) < 2:
            vol_line.append(math.nan)
            continue
        mean = sum(window) / len(window)
        var = sum((r - mean) ** 2 for r in window) / (len(window) - 1)
        vol_line.append(math.sqrt(var))
    valid = [v for v in vol_line if not math.isnan(v)]
    vol_median = sorted(valid)[len(valid) // 2] if valid else math.nan
    regimes: list[Regime] = []
    for i in range(len(bars)):
        tl = trend_line[i]
        trend = (
            "UP"
            if not math.isnan(tl) and closes[i] > tl * 1.001
            else "DOWN"
            if not math.isnan(tl) and closes[i] < tl * 0.999
            else "FLAT"
        )
        vl = vol_line[i]
        vol = "HIGH" if not math.isnan(vl) and vl >= vol_median else "LOW"
        regimes.append(Regime(trend, vol, f"{trend}/{vol}"))
    return regimes


def drawdown_series(equity: Sequence[float]) -> list[float]:
    """Running drawdown of an equity curve: 0.0 = at peak, 0.15 = -15%."""
    peak = -math.inf
    out: list[float] = []
    for e in equity:
        peak = max(peak, e)
        out.append((e / peak) - 1.0 if peak > 0 else 0.0)
    return out


def max_drawdown(equity: Sequence[float]) -> float:
    return min(drawdown_series(equity), default=0.0)


def cost_per_trade(bp: float) -> float:
    """One-way transaction cost as a fraction (10 bp -> 0.001)."""
    return bp / 10000.0


def trade_count(decisions: Iterable["object"]) -> int:  # noqa: ANN001 - forward ref
    return sum(1 for d in decisions if getattr(d, "action", "HOLD") != "HOLD")

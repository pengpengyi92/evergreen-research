"""Tests for the Quant×AI evaluation harness (harness/).

Integration tests run against the bundled public fixture
(data/market/spx_daily.csv) and are deterministic; unit tests use small
hand-built series.
"""

import json
import tempfile
import unittest
from pathlib import Path

from harness.agent import (
    ACTION_BUY,
    ACTION_HOLD,
    ACTION_SELL,
    AgentState,
    Decision,
    DisciplinedAgent,
    RecklessAgent,
    build_agent,
    extract_declared_strategy,
)
from harness.checks import (
    C1_BEHAVIORAL,
    C1_DISCLOSURE,
    C2_BEHAVIORAL,
    C2_DISCLOSURE,
    C3_BEHAVIORAL,
    C3_DISCLOSURE,
    C4_BEHAVIORAL,
    C4_DISCLOSURE,
    check_c1_strategy_drift,
    check_c3_drawdown,
    check_c4_tool_failures,
)
from harness.engine import ToolInjector, replay
from harness.market import (
    Bar,
    cost_per_trade,
    daily_returns,
    drawdown_series,
    load_ohlcv,
    max_drawdown,
    segment_regimes,
    sma,
)
from harness.report import render_json, render_markdown, run_full

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "market" / "spx_daily.csv"


def _bars(closes: list[float]) -> list[Bar]:
    return [
        Bar(date=f"2026-01-{i+1:02d}", open=c, high=c, low=c, close=c, volume=1.0)
        for i, c in enumerate(closes)
    ]


class HoldAgent:
    """Never trades; used to exercise no-breach / no-failure paths."""

    declared_strategy = "hold"
    risk_limit = -0.10
    name = "hold"

    def observe(self, state: AgentState) -> Decision:
        return Decision(ACTION_HOLD, 0.0, "holding", "hold")


class MarketTest(unittest.TestCase):
    def test_fixture_loads_and_ranges(self) -> None:
        bars = load_ohlcv(FIXTURE)
        self.assertEqual(len(bars), 1255)
        self.assertEqual(bars[0].date, "2021-08-23")
        self.assertEqual(bars[-1].date, "2026-08-21")
        self.assertTrue(all(b.close > 0 for b in bars))

    def test_regimes_span_both_axes(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        self.assertEqual(len(regimes), len(bars))
        trends = {r.trend for r in regimes}
        vols = {r.vol for r in regimes}
        self.assertTrue({"UP", "DOWN"} <= trends)
        self.assertTrue({"LOW", "HIGH"} <= vols)

    def test_drawdown_series_hand_built(self) -> None:
        equity = [100.0, 120.0, 90.0, 95.0, 60.0]
        dd = drawdown_series(equity)
        self.assertEqual(dd[0], 0.0)
        self.assertEqual(dd[1], 0.0)  # new peak
        self.assertAlmostEqual(dd[2], -0.25)
        self.assertAlmostEqual(dd[3], -0.2083333, places=5)
        self.assertAlmostEqual(max_drawdown(equity), -0.5)

    def test_sma_and_returns(self) -> None:
        closes = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertEqual(sma(closes, 3)[-1], 4.0)
        rets = daily_returns(_bars(closes))
        self.assertAlmostEqual(rets[-1], 0.25)

    def test_cost_per_trade(self) -> None:
        self.assertAlmostEqual(cost_per_trade(10.0), 0.001)
        self.assertAlmostEqual(cost_per_trade(0.0), 0.0)


class StrategyExtractTest(unittest.TestCase):
    def test_extraction(self) -> None:
        self.assertEqual(extract_declared_strategy("trend-following — ride"), "trend-following")
        self.assertEqual(extract_declared_strategy("buy-the-dip mean-reversion"), "mean-reversion")
        self.assertEqual(extract_declared_strategy("momentum — sell weakness"), "momentum")
        self.assertEqual(extract_declared_strategy("holding quietly"), "unspecified")


class CheckC1Test(unittest.TestCase):
    def test_reckless_drifts_with_regime(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        trace = replay(RecklessAgent(), bars, regimes)
        res = check_c1_strategy_drift(trace)
        self.assertGreater(res.details["max_drift"], 0.5)
        self.assertLess(res.behavioral, C1_BEHAVIORAL)
        self.assertLess(res.disclosure, C1_DISCLOSURE)
        self.assertFalse(res.passed)


class CheckC3Test(unittest.TestCase):
    def test_no_breach_is_not_exercised_and_passes(self) -> None:
        bars = _bars([100.0 + i for i in range(200)])  # steady climb
        regimes = segment_regimes(bars, trend_window=5, vol_window=5)
        trace = replay(HoldAgent(), bars, regimes)
        res = check_c3_drawdown(trace, HoldAgent())
        self.assertFalse(res.exercised)
        self.assertTrue(res.passed)

    def test_disciplined_reduces_after_breach(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        trace = replay(DisciplinedAgent(), bars, regimes)
        res = check_c3_drawdown(trace, DisciplinedAgent())
        self.assertTrue(res.exercised)
        self.assertGreaterEqual(res.behavioral, C3_BEHAVIORAL)
        self.assertGreaterEqual(res.disclosure, C3_DISCLOSURE)
        self.assertTrue(res.passed)

    def test_reckless_never_reduces(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        trace = replay(RecklessAgent(), bars, regimes)
        res = check_c3_drawdown(trace, RecklessAgent())
        self.assertEqual(res.details["exposure_reduction"], 0.0)
        self.assertFalse(res.passed)


class CheckC4Test(unittest.TestCase):
    def test_no_injection_not_exercised(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        trace = replay(DisciplinedAgent(), bars, regimes, injector=ToolInjector())
        res = check_c4_tool_failures(trace)
        self.assertFalse(res.exercised)
        self.assertTrue(res.passed)

    def test_disciplined_never_trades_on_stale(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        injector = ToolInjector(stale_rate=0.1, error_rate=0.05, seed=3)
        trace = replay(DisciplinedAgent(), bars, regimes, injector=injector)
        stale = [s for s in trace.steps if s.tool_status == "stale"]
        self.assertTrue(stale)
        self.assertTrue(all(s.decision.action == ACTION_HOLD for s in stale))
        res = check_c4_tool_failures(trace)
        self.assertEqual(res.behavioral, 1.0)
        self.assertTrue(res.passed)

    def test_reckless_trades_on_stale(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        injector = ToolInjector(stale_rate=0.1, error_rate=0.05, seed=3)
        trace = replay(RecklessAgent(), bars, regimes, injector=injector)
        stale = [s for s in trace.steps if s.tool_status == "stale"]
        self.assertTrue(all(s.decision.action != ACTION_HOLD for s in stale))
        res = check_c4_tool_failures(trace)
        self.assertEqual(res.behavioral, 0.0)
        self.assertFalse(res.passed)


class DiscriminationTest(unittest.TestCase):
    """The core claim of Paper 3 §6: the harness tells discipline from
    recklessness. Runs on the real public fixture."""

    def test_disciplined_passes_all_checks(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        report = run_full(DisciplinedAgent(), bars, regimes, data_meta={"bars": len(bars)})
        self.assertEqual(report["summary"]["passed"], 4)
        for c in report["checks"]:
            self.assertTrue(c["passed"], c["name"])

    def test_reckless_fails_all_checks(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        report = run_full(RecklessAgent(), bars, regimes, data_meta={"bars": len(bars)})
        self.assertEqual(report["summary"]["passed"], 0)
        for c in report["checks"]:
            self.assertFalse(c["passed"], c["name"])

    def test_cost_tiers_move_volume_for_disciplined_only(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        disc = run_full(DisciplinedAgent(), bars, regimes)
        reck = run_full(RecklessAgent(), bars, regimes)
        disc_c2 = disc["checks"][1]["details"]["trades_by_cost_bp"]
        reck_c2 = reck["checks"][1]["details"]["trades_by_cost_bp"]
        self.assertLess(disc_c2[30.0], disc_c2[0.0])
        self.assertEqual(reck_c2[0.0], reck_c2[30.0])


class ReportTest(unittest.TestCase):
    def test_json_schema_and_markdown(self) -> None:
        bars = load_ohlcv(FIXTURE)
        regimes = segment_regimes(bars)
        report = run_full(build_agent("disciplined"), bars, regimes, data_meta={"source": "test"})
        doc = json.loads(render_json(report))
        self.assertEqual(len(doc["checks"]), 4)
        self.assertIn("harness_version", doc)
        md = render_markdown(report)
        self.assertIn("Scope honesty", md)
        self.assertIn("C1 strategy drift", md)
        self.assertIn("investment advice", md)

    def test_demo_writes_both_samples(self) -> None:
        # exercises the CLI end-to-end without network
        from harness.cli import cmd_demo

        with tempfile.TemporaryDirectory() as tmp:
            args = type("A", (), {"out": tmp, "cost": 10.0, "stale": 0.05, "error": 0.03})()
            rc = cmd_demo(args)
            out = Path(tmp)
            self.assertTrue((out / "sample-disciplined.md").exists())
            self.assertTrue((out / "sample-disciplined.json").exists())
            self.assertTrue((out / "sample-reckless.md").exists())
            self.assertEqual(rc, 1)  # reckless fails by design


if __name__ == "__main__":
    unittest.main()

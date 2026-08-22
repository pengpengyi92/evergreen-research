"""CLI: python -m harness run|demo.

Zero-dependency, mirroring the presearch CLI style.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .agent import REFERENCE_AGENTS, build_agent
from .market import load_ohlcv, segment_regimes
from .report import render_json, render_markdown, run_full

# bundled public fixture (provenance in data/market/PROVENANCE.md)
FIXTURE = Path(__file__).resolve().parent.parent / "data" / "market" / "spx_daily.csv"
FIXTURE_SHA256 = "5b6e7115779b8027a9b613b64ba6731c77c3dfe6c5f9019fbc8f5e9672fdb61d"


def _data_meta(bars_path: Path, bars: list) -> dict:
    return {
        "source": "Yahoo Finance ^GSPC daily (query2.finance.yahoo.com/v8/finance/chart)",
        "retrieved": "2026-08-23",
        "path": str(bars_path),
        "sha256": FIXTURE_SHA256 if bars_path.resolve() == FIXTURE.resolve() else "n/a",
        "bars": len(bars),
        "start": bars[0].date,
        "end": bars[-1].date,
    }


def _load(agent_name: str, data_path: str) -> tuple:
    agent = build_agent(agent_name)
    path = Path(data_path)
    bars = load_ohlcv(path)
    regimes = segment_regimes(bars)
    return agent, bars, regimes, _data_meta(path, bars)


def cmd_run(args: argparse.Namespace) -> int:
    agent, bars, regimes, meta = _load(args.agent, args.data)
    report = run_full(
        agent, bars, regimes, data_meta=meta,
        stated_cost_bp=args.cost, stale_rate=args.stale, error_rate=args.error,
    )
    text = render_json(report) if args.format == "json" else render_markdown(report)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"[harness] wrote {args.out}")
    else:
        print(text)
    return 0 if report["summary"]["passed"] == report["summary"]["total"] else 1


def cmd_demo(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rc = 0
    for name in sorted(REFERENCE_AGENTS):
        agent, bars, regimes, meta = _load(name, str(FIXTURE))
        report = run_full(agent, bars, regimes, data_meta=meta,
                          stated_cost_bp=args.cost, stale_rate=args.stale, error_rate=args.error)
        out = out_dir / f"sample-{name}.md"
        out.write_text(render_markdown(report) + "\n", encoding="utf-8")
        out_json = out_dir / f"sample-{name}.json"
        out_json.write_text(render_json(report) + "\n", encoding="utf-8")
        status = "PASS" if report["summary"]["passed"] == report["summary"]["total"] else "FAIL"
        print(f"[harness] {name}: {report['summary']['passed']}/{report['summary']['total']} "
              f"passed ({status}) -> {out}")
        if status == "FAIL":
            rc = 1
    return rc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="harness", description="Quant×AI evaluation harness")
    p.add_argument("--version", action="version", version=f"harness {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="evaluate one agent")
    run.add_argument("--agent", required=True, choices=sorted(REFERENCE_AGENTS),
                     help="reference agent to evaluate")
    run.add_argument("--data", default=str(FIXTURE), help="OHLCV CSV (date,open,high,low,close,volume)")
    run.add_argument("--cost", type=float, default=10.0, help="stated one-way cost in bp")
    run.add_argument("--stale", type=float, default=0.05, help="stale-data injection rate")
    run.add_argument("--error", type=float, default=0.03, help="broker-error injection rate")
    run.add_argument("--format", choices=["md", "json"], default="md")
    run.add_argument("--out", default="", help="write report to this path")
    run.set_defaults(func=cmd_run)

    demo = sub.add_parser("demo", help="run both reference agents on the bundled fixture")
    demo.add_argument("--cost", type=float, default=10.0)
    demo.add_argument("--stale", type=float, default=0.05)
    demo.add_argument("--error", type=float, default=0.03)
    demo.add_argument("--out", default="docs/harness", help="output directory")
    demo.set_defaults(func=cmd_demo)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

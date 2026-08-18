"""Weekly sweep pipeline: fetch -> structure -> cluster -> publish."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evergreen import arxiv_client, pillars as pillars_config
from evergreen.database import PaperDatabase
from evergreen.structurer import structure_entry


def _cluster_signals(records: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    """Cross-pillar convergence: a method tag spanning >= 2 pillars."""
    method_pillars: dict[str, set[str]] = {}
    method_count: dict[str, int] = {}
    for record in records:
        for method in record.get("methods", []):
            method_pillars.setdefault(method, set()).add(record.get("pillar", "?"))
            method_count[method] = method_count.get(method, 0) + 1

    signals: list[dict[str, Any]] = []
    for method, span in sorted(
        method_pillars.items(), key=lambda item: -method_count[item[0]]
    ):
        if len(span) >= 2 and method_count[method] >= 3:
            signals.append(
                {
                    "method": method,
                    "papers": method_count[method],
                    "spanning_pillars": sorted(span),
                    "claim": (
                        f"{method} is converging across {len(span)} pillars "
                        f"({method_count[method]} papers in the current window)."
                    ),
                }
            )
        if len(signals) >= limit:
            break
    return signals


def run_backfill(
    data_root: Path,
    windows: list[tuple[int, int]],
    per_pillar: int = 30,
    quiet: bool = False,
) -> dict[str, Any]:
    """Historical backfill over non-overlapping (days_back, until_days_back)
    windows; the database dedups by paper id."""
    swept_on = datetime.now(UTC).isoformat()
    db = PaperDatabase(data_root)
    structured: list[dict[str, Any]] = []
    failures: list[str] = []

    for days_back, until_days_back in windows:
        for pillar, spec in pillars_config.PILLARS.items():
            categories = list(spec["categories"])  # type: ignore[arg-type]
            terms = str(spec["terms"])  # type: ignore[arg-type]
            try:
                entries = arxiv_client.search_recent(
                    categories,
                    max_results=per_pillar,
                    days_back=days_back,
                    until_days_back=until_days_back,
                    terms=terms,
                )
            except Exception as exc:
                failures.append(f"{pillar} ({until_days_back}-{days_back}d): {exc}")
                entries = []
            for entry in entries:
                structured.append(structure_entry(entry, pillar, swept_on))

    added = db.upsert_many(structured)
    if not quiet:
        print(
            f"[evergreen] backfill fetched {len(structured)} papers over "
            f"{windows}, {added} new records"
        )
    if failures and not quiet:
        for failure in failures:
            print(f"[evergreen] degraded pillar: {failure}")
    return {
        "swept_on": swept_on,
        "fetched": len(structured),
        "new_records": added,
        "failures": failures,
        "total_db": len(db.load()),
    }


def run_weekly(
    data_root: Path,
    max_per_pillar: int | None = None,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run one weekly sweep. Returns a summary dict."""
    swept_on = datetime.now(UTC).isoformat()
    db = PaperDatabase(data_root)
    structured: list[dict[str, Any]] = []
    failures: list[str] = []

    for pillar, spec in pillars_config.PILLARS.items():
        categories = list(spec["categories"])  # type: ignore[arg-type]
        terms = str(spec["terms"])  # type: ignore[arg-type]
        days_back = int(spec["days_back"])  # type: ignore[arg-type]
        max_results = int(spec["max"] if max_per_pillar is None else max_per_pillar)  # type: ignore[arg-type]
        try:
            entries = arxiv_client.search_recent(
                categories, max_results=max_results, days_back=days_back, terms=terms
            )
        except Exception as exc:  # network failure degrades gracefully
            failures.append(f"{pillar}: {exc}")
            entries = []
        if not entries:
            failures.append(f"{pillar}: no entries returned")
        for entry in entries:
            structured.append(structure_entry(entry, pillar, swept_on))

    added = db.upsert_many(structured)
    signals = _cluster_signals(structured)
    if not quiet:
        print(
            f"[evergreen] swept {len(structured)} papers, {added} new records, "
            f"{len(signals)} cross-pillar signals"
        )
    if failures and not quiet:
        for failure in failures:
            print(f"[evergreen] degraded pillar: {failure}")

    return {
        "swept_on": swept_on,
        "fetched": len(structured),
        "new_records": added,
        "signals": signals,
        "failures": failures,
        "total_db": len(db.load()),
    }

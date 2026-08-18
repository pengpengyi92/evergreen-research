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


def run_verification(
    data_root: Path,
    pillar: str,
    top_n: int = 10,
    quiet: bool = False,
) -> dict[str, Any]:
    """M2 gate: full-text verification for core-corpus candidates.

    Pulls ar5iv HTML for the newest unverified papers in a pillar, re-runs
    the deterministic taggers on full text, and records verification
    metadata on the database record.
    """
    from datetime import UTC, datetime

    from evergreen import fulltext
    from evergreen.structurer import detect_benchmarks, detect_methods, detect_models

    db = PaperDatabase(data_root)
    candidates = [
        record
        for record in db.load()
        if record.get("pillar") == pillar and not record.get("verified")
    ]
    candidates.sort(key=lambda record: record.get("published", ""), reverse=True)
    candidates = candidates[:top_n]

    verified = 0
    unavailable = 0
    failed = 0
    for record in candidates:
        record_id = record["id"]
        try:
            html_payload, source = fulltext.fetch_fulltext(record.get("arxiv_id", ""))
        except Exception as exc:
            failed += 1
            db.update_record(
                record_id,
                {
                    "verified": False,
                    "verification": {
                        "source": "none",
                        "status": "fetch-error",
                        "error": str(exc)[:200],
                        "checked_on": datetime.now(UTC).isoformat(),
                    },
                },
            )
            if not quiet:
                print(f"[verify] {record_id}: fetch error {exc}")
            continue
        if not html_payload:
            unavailable += 1
            db.update_record(
                record_id,
                {
                    "verified": False,
                    "verification": {
                        "source": source,
                        "status": "unavailable",
                        "checked_on": datetime.now(UTC).isoformat(),
                    },
                },
            )
            continue
        text = fulltext.html_to_text(html_payload)
        methods = detect_methods(text)
        benchmarks = detect_benchmarks(text)
        models = detect_models(text)
        stored_methods = set(record.get("methods", []))
        matched = sorted(stored_methods & set(methods))
        is_verified = len(text) > 5000
        db.update_record(
            record_id,
            {
                "verified": is_verified,
                "verification": {
                    "source": source,
                    "status": "fulltext-verified" if is_verified else "insufficient-text",
                    "fulltext_chars": len(text),
                    "fulltext_methods": methods[:12],
                    "fulltext_benchmarks": benchmarks[:12],
                    "fulltext_models": models[:10],
                    "matched_methods": matched,
                    "checked_on": datetime.now(UTC).isoformat(),
                },
            },
        )
        if is_verified:
            verified += 1
        if not quiet:
            print(
                f"[verify] {record_id}: {'verified' if is_verified else 'short-text'} "
                f"via {source} ({len(text)} chars, matched {len(matched)}/{len(stored_methods)} methods)"
            )
    return {
        "pillar": pillar,
        "attempted": len(candidates),
        "verified": verified,
        "unavailable": unavailable,
        "failed": failed,
    }


def run_citations(
    data_root: Path,
    pillar: str,
    top_n: int = 25,
    verified_only: bool = True,
    source: str = "openalex",
    quiet: bool = False,
) -> dict[str, Any]:
    """M3 gate: batch citation tracking for core-corpus papers.

    source "openalex" (default) is keyless; "s2" uses Semantic Scholar
    (S2_API_KEY recommended). Only successful fetches are persisted.
    """
    db = PaperDatabase(data_root)
    candidates = [record for record in db.load() if record.get("pillar") == pillar]
    if verified_only:
        candidates = [record for record in candidates if record.get("verified")]
    candidates.sort(key=lambda record: record.get("published", ""), reverse=True)
    candidates = candidates[:top_n]

    if source == "openalex":
        from evergreen import openalex
        from evergreen.citations import CitationStore

        store = CitationStore(data_root)
        known = store.load()
        fresh = [
            record
            for record in candidates
            if record.get("arxiv_id") and f"arXiv:{record['arxiv_id'].split('/abs/')[-1]}" not in known
        ]
        fetched = openalex.batch_citations(fresh, quiet=quiet)
        for item in fetched:
            base = item["arxiv_id"].split("/abs/")[-1]
            if not base.lower().startswith("arxiv:"):
                base = f"arXiv:{base}"
            item["arxiv_id"] = base
            item["source"] = "openalex"
        stored = store.upsert(fetched)
        results: dict[str, Any] = {
            "source": "openalex",
            "ok": len(fetched),
            "rate_limited": 0,
            "failed": len(fresh) - len(fetched),
            "skipped_existing": len(candidates) - len(fresh),
            "stored": stored,
            "stats": store.stats(),
        }
        return results

    from evergreen import citations as s2

    store = s2.CitationStore(data_root)
    known = store.load()
    results = {"source": "s2", "ok": 0, "rate_limited": 0, "failed": 0, "skipped_existing": 0}
    to_store: list[dict[str, Any]] = []
    for record in candidates:
        arxiv_id = record.get("arxiv_id", "")
        if s2.normalize_arxiv_id(arxiv_id) in known:
            results["skipped_existing"] += 1
            continue
        try:
            data = s2.paper_by_arxiv_id(arxiv_id)
        except Exception as exc:
            results["failed"] += 1
            if not quiet:
                print(f"[citations] {arxiv_id}: {exc}")
            continue
        if data.get("error") == "rate_limited":
            results["rate_limited"] += 1
            if not quiet:
                print(f"[citations] {arxiv_id}: rate limited (set S2_API_KEY for batch runs)")
            continue
        results["ok"] += 1
        data["arxiv_id"] = s2.normalize_arxiv_id(arxiv_id)
        to_store.append(data)
    results["stored"] = store.upsert(to_store)
    results["stats"] = store.stats()
    return results


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
        "swept_records": structured,
    }

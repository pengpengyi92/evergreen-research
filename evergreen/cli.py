from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evergreen import __version__
from evergreen import arxiv_client
from evergreen.database import PaperDatabase
from evergreen.pipeline import run_backfill, run_weekly
from evergreen.report import write_docs_landing, write_index, write_survey_outline, write_weekly

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evergreen")
    subparsers = parser.add_subparsers(dest="command", required=True)

    weekly = subparsers.add_parser("weekly")
    weekly.add_argument("--max-per-pillar", type=int, default=None)
    weekly.add_argument("--data-root", default=str(PROJECT_ROOT / "data"))
    weekly.add_argument("--docs-root", default=str(PROJECT_ROOT / "docs"))

    backfill = subparsers.add_parser("backfill")
    backfill.add_argument(
        "--windows",
        default="0-360,360-1080,1080-2160",
        help="comma-separated non-overlapping day windows as UNTIL-DAYSBACK "
        "(e.g. 0-360 = the last year)",
    )
    backfill.add_argument("--per-pillar", type=int, default=30)
    backfill.add_argument("--data-root", default=str(PROJECT_ROOT / "data"))
    backfill.add_argument("--docs-root", default=str(PROJECT_ROOT / "docs"))

    fetch = subparsers.add_parser("fetch")
    fetch.add_argument("--query", default=None)
    fetch.add_argument("--categories", default="cs.AI,cs.LG,cs.CL")
    fetch.add_argument("--max", type=int, default=20)
    fetch.add_argument("--days", type=int, default=14)

    db_parser = subparsers.add_parser("db")
    db_sub = db_parser.add_subparsers(dest="db_command", required=True)
    db_stats = db_sub.add_parser("stats")
    db_stats.add_argument("--data-root", default=str(PROJECT_ROOT / "data"))

    survey = subparsers.add_parser("survey")
    survey.add_argument("--data-root", default=str(PROJECT_ROOT / "data"))

    version = subparsers.add_parser("version")

    args = parser.parse_args(argv)

    if args.command == "weekly":
        data_root = Path(args.data_root)
        summary = run_weekly(data_root, max_per_pillar=args.max_per_pillar)
        db = PaperDatabase(data_root)
        weekly_path = write_weekly(db, summary, data_root / "weekly")
        index_path = write_index(db, data_root)
        survey_path = write_survey_outline(db, data_root / "survey")
        docs_path = write_docs_landing(db, Path(args.docs_root))
        return _emit(
            {
                "summary": summary,
                "weekly": str(weekly_path),
                "index": str(index_path),
                "survey_outline": str(survey_path),
                "docs_landing": str(docs_path),
            }
        )
    if args.command == "backfill":
        data_root = Path(args.data_root)
        windows: list[tuple[int, int]] = []
        for part in args.windows.split(","):
            part = part.strip()
            if not part:
                continue
            until_str, _, back_str = part.partition("-")
            windows.append((int(back_str), int(until_str)))
        summary = run_backfill(data_root, windows, per_pillar=args.per_pillar)
        db = PaperDatabase(data_root)
        index_path = write_index(db, data_root)
        survey_path = write_survey_outline(db, data_root / "survey")
        docs_path = write_docs_landing(db, Path(args.docs_root))
        return _emit(
            {
                "summary": summary,
                "index": str(index_path),
                "survey_outline": str(survey_path),
                "docs_landing": str(docs_path),
            }
        )
    if args.command == "fetch":
        if args.query:
            entries = arxiv_client.fetch_entries(args.query, max_results=args.max)
        else:
            categories = [part.strip() for part in args.categories.split(",") if part.strip()]
            entries = arxiv_client.search_recent(
                categories, max_results=args.max, days_back=args.days
            )
        return _emit(entries)
    if args.command == "db" and args.db_command == "stats":
        db = PaperDatabase(Path(args.data_root))
        return _emit(db.stats())
    if args.command == "survey":
        db = PaperDatabase(Path(args.data_root))
        path = write_survey_outline(db, Path(args.data_root) / "survey")
        print(path.read_text(encoding="utf-8"))
        return 0
    if args.command == "version":
        print(__version__)
        return 0
    raise AssertionError("unreachable")


def _emit(data: Any) -> int:
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

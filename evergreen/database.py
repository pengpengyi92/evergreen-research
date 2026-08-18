"""Append-only JSONL paper database with deduplication and stats."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


class PaperDatabase:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "papers.jsonl"

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except ValueError:
                    continue
        return records

    def upsert_many(self, records: list[dict[str, Any]]) -> int:
        """Append new records; returns how many were newly added."""
        existing = {record["id"] for record in self.load()}
        added = 0
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for record in records:
                if record["id"] in existing:
                    continue
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                existing.add(record["id"])
                added += 1
        return added

    def stats(self) -> dict[str, Any]:
        records = self.load()
        pillars = Counter(record.get("pillar", "?") for record in records)
        methods = Counter(
            method for record in records for method in record.get("methods", [])
        )
        return {
            "total_papers": len(records),
            "by_pillar": dict(pillars.most_common()),
            "top_methods": dict(methods.most_common(12)),
            "newest_swept_on": max(
                (record.get("swept_on", "") for record in records), default=""
            ),
        }

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        records = self.load()
        records.sort(key=lambda record: record.get("published", ""), reverse=True)
        return records[:limit]

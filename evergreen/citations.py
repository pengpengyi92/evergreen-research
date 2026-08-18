"""Semantic Scholar citation tracking for the Evergreen corpus.

Batch-fetches citation metadata for verified papers and stores it in an
append-only `data/citations.jsonl`. Anonymous access is rate-limited hard;
set S2_API_KEY (free) for reliable batch runs. Degrades gracefully: a
rate-limited fetch is recorded as `status: rate_limited`, not a crash.

Environment override for the cache dir (used by tests):
    EVERGREEN_S2_CACHE=<path>
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.semanticscholar.org/graph/v1/paper"
USER_AGENT = "evergreen-research/0.3 (open-source frontier-AI research; stdlib client)"
REQUEST_GAP_SECONDS = 1.1
CACHE_TTL_SECONDS = 24 * 3600
MAX_RETRIES = 4

_last_request_ts = 0.0

FIELDS = "title,citationCount,influentialCitationCount,publicationDate,externalIds,venue"


def _cache_root() -> Path:
    override = os.environ.get("EVERGREEN_S2_CACHE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / ".cache" / "s2"


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return _cache_root() / f"{digest}.json"


def _load_cache(key: str) -> dict[str, Any] | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        age = time.time() - path.stat().st_mtime
        if age > CACHE_TTL_SECONDS:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        return None
    return None


def _save_cache(key: str, data: dict[str, Any]) -> None:
    try:
        path = _cache_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _rate_limit() -> None:
    global _last_request_ts
    elapsed = time.monotonic() - _last_request_ts
    if _last_request_ts and elapsed < REQUEST_GAP_SECONDS:
        time.sleep(REQUEST_GAP_SECONDS - elapsed)
    _last_request_ts = time.monotonic()


def normalize_arxiv_id(arxiv_id: str) -> str:
    base = arxiv_id.split("/abs/")[-1]
    if not base.lower().startswith("arxiv:"):
        base = f"arXiv:{base}"
    return base


def paper_by_arxiv_id(
    arxiv_id: str,
    use_cache: bool = True,
    fetch_func: Any | None = None,
) -> dict[str, Any]:
    """Fetch S2 metadata for one arXiv id; degrades to a rate_limited record."""
    normalized = normalize_arxiv_id(arxiv_id)
    if use_cache:
        cached = _load_cache(normalized)
        if cached is not None:
            return cached

    params = {"fields": FIELDS}
    url = f"{API_URL}/{urllib.parse.quote(normalized, safe=':')}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    rate_limited = False
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit()
            if fetch_func is not None:
                data = fetch_func(url)
            else:
                headers = {"User-Agent": USER_AGENT}
                api_key = os.environ.get("S2_API_KEY")
                if api_key:
                    headers["x-api-key"] = api_key
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = json.loads(response.read().decode("utf-8", errors="replace"))
            _save_cache(normalized, data)
            return data
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                rate_limited = True
            if attempt + 1 < MAX_RETRIES:
                time.sleep(4 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt + 1 < MAX_RETRIES:
                time.sleep(3 * (attempt + 1))
    if rate_limited:
        return {
            "arxiv_id": normalized,
            "citationCount": None,
            "influentialCitationCount": None,
            "error": "rate_limited",
            "hint": "set S2_API_KEY (free at semanticscholar.org) for reliable batch access",
        }
    raise RuntimeError(f"S2 fetch failed after {MAX_RETRIES} attempts: {last_error}")


class CitationStore:
    """Append-only JSONL citation store keyed by normalized arXiv id."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "citations.jsonl"

    def load(self) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        if not self.path.exists():
            return index
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                key = record.get("arxiv_id") or record.get("id") or ""
                if key:
                    index[key] = record
        return index

    def upsert(self, records: list[dict[str, Any]]) -> int:
        existing = self.load()
        added = 0
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for record in records:
                key = record.get("arxiv_id") or ""
                if not key or key in existing:
                    continue
                record = {"id": key, **record, "fetched_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                existing[key] = record
                added += 1
        return added

    def stats(self) -> dict[str, Any]:
        records = list(self.load().values())
        counts = [record.get("citationCount") for record in records if record.get("citationCount") is not None]
        if not counts:
            return {"tracked": len(records), "with_citations": 0}
        counts.sort()
        middle = len(counts) // 2
        if len(counts) % 2:
            median = counts[middle]
        else:
            median = (counts[middle - 1] + counts[middle]) / 2
        return {
            "tracked": len(records),
            "with_citations": len(counts),
            "median_citations": median,
            "max_citations": counts[-1],
            "total_citations": sum(counts),
            "total_influential": sum(
                record.get("influentialCitationCount") or 0 for record in records
            ),
        }

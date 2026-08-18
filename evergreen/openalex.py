"""OpenAlex citation connector (keyless).

OpenAlex (openalex.org) is a fully open scholarly database: no API key
required, 10 req/s polite pool, citation counts included. Used as the
default citation source when no S2_API_KEY is configured, and as the
fallback when S2 is rate-limited.

Environment override for the cache dir (used by tests):
    EVERGREEN_OPENALEX_CACHE=<path>
"""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.openalex.org/works"
USER_AGENT = "evergreen-research/0.4 (open-source frontier-AI research; contact: pengpengyi92@gmail.com)"
REQUEST_GAP_SECONDS = 0.5
CACHE_TTL_SECONDS = 7 * 24 * 3600
MAX_RETRIES = 3

_last_request_ts = 0.0


def _cache_root() -> Path:
    override = os.environ.get("EVERGREEN_OPENALEX_CACHE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / ".cache" / "openalex"


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


def _author_surname_overlap(record: dict[str, Any], work: dict[str, Any]) -> int:
    record_surnames = {
        name.split()[-1].lower().strip(".,") for name in record.get("authors", []) if name
    }
    work_surnames = {
        author.get("author", {}).get("display_name", "").split()[-1].lower()
        for author in work.get("authorships", [])
    }
    return len(record_surnames & work_surnames)


def paper_by_title(record: dict[str, Any], use_cache: bool = True) -> dict[str, Any]:
    """Look up a work in OpenAlex by title search; None when not found."""
    title = re.sub(r"[^A-Za-z0-9 ]+", " ", record.get("title", "")).strip()
    if not title:
        return {"error": "no-title"}
    key = "title-" + title.lower()
    if use_cache:
        cached = _load_cache(key)
        if cached is not None:
            return cached

    params = {
        "filter": f"title.search:{title}",
        "per-page": 5,
        "mailto": "pengpengyi92@gmail.com",
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit()
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            works = payload.get("results", [])
            best: dict[str, Any] | None = None
            best_overlap = -1
            for work in works:
                work_title = (work.get("title") or "").lower()
                if not work_title:
                    continue
                overlap = _author_surname_overlap(record, work)
                score = overlap
                if work_title == title.lower():
                    score += 10
                if score > best_overlap:
                    best_overlap = score
                    best = work
            result: dict[str, Any]
            if best is None or (best_overlap < 1 and best.get("title", "").lower() != title.lower()):
                result = {"error": "not-found"}
            else:
                result = {
                    "source": "openalex",
                    "openalex_id": best.get("id", ""),
                    "title": best.get("title"),
                    "citationCount": best.get("cited_by_count"),
                    "influentialCitationCount": None,
                    "publicationDate": best.get("publication_date"),
                    "venue": (best.get("primary_location") or {}).get("source", {}).get("display_name")
                    if (best.get("primary_location") or {}).get("source")
                    else None,
                    "surname_overlap": best_overlap,
                }
            _save_cache(key, result)
            return result
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, http.client.HTTPException) as exc:
            last_error = exc
            if attempt + 1 < MAX_RETRIES:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"OpenAlex fetch failed after {MAX_RETRIES} attempts: {last_error}")


def batch_citations(records: list[dict[str, Any]], quiet: bool = False) -> list[dict[str, Any]]:
    """Fetch citation metadata for a batch of DB records (keyless)."""
    results: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        try:
            data = paper_by_title(record)
        except Exception as exc:
            if not quiet:
                print(f"[openalex] {record.get('arxiv_id', '?')}: {exc}")
            continue
        if data.get("error"):
            if not quiet:
                print(f"[openalex] {record.get('arxiv_id', '?')}: {data.get('error')}")
            continue
        data["arxiv_id"] = record.get("arxiv_id", "")
        results.append(data)
        if not quiet and index % 5 == 0:
            print(f"[openalex] {index}/{len(records)}")
    return results

"""Rate-limited arXiv API client (stdlib-only).

Etiquette: >=3s between requests. Robustness: retries with backoff and
salvage of complete <entry> blocks from truncated responses. Cache:
time-boxed on-disk store so re-runs are cheap and offline runs degrade
gracefully.

Environment override for the cache dir (used by tests):
    PRESEARCH_ARXIV_CACHE=<path>
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
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
USER_AGENT = "p-research/0.1 (open-source frontier-AI research; stdlib client)"
REQUEST_GAP_SECONDS = 3.1
CACHE_TTL_SECONDS = 6 * 3600
MAX_RETRIES = 3

_last_request_ts = 0.0


def _cache_root() -> Path:
    override = os.environ.get("PRESEARCH_ARXIV_CACHE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / ".cache" / "arxiv"


def _rate_limit() -> None:
    global _last_request_ts
    elapsed = time.monotonic() - _last_request_ts
    if _last_request_ts and elapsed < REQUEST_GAP_SECONDS:
        time.sleep(REQUEST_GAP_SECONDS - elapsed)
    _last_request_ts = time.monotonic()


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return _cache_root() / f"{digest}.json"


def _load_cache(key: str) -> list[dict[str, Any]] | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        age = time.time() - path.stat().st_mtime
        if age > CACHE_TTL_SECONDS:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (OSError, ValueError):
        return None
    return None


def _save_cache(key: str, entries: list[dict[str, Any]]) -> None:
    try:
        path = _cache_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # cache is best-effort only


def parse_atom(payload: str) -> list[dict[str, Any]]:
    """Parse an arXiv Atom API payload into plain entry dicts."""
    root = ET.fromstring(payload)
    entries: list[dict[str, Any]] = []
    for element in root.findall("atom:entry", ATOM_NS):
        title = (element.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        summary = (element.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
        published = element.findtext("atom:published", default="", namespaces=ATOM_NS) or ""
        updated = element.findtext("atom:updated", default="", namespaces=ATOM_NS) or ""
        arxiv_id = (element.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        links = element.findall("atom:link", ATOM_NS)
        url = next(
            (link.get("href", "") for link in links if link.get("rel") in (None, "alternate")),
            "",
        )
        if not url and links:
            url = links[0].get("href", "")
        primary_element = element.find("arxiv:primary_category", ATOM_NS)
        primary = ""
        if primary_element is not None:
            primary = (primary_element.get("term") or "").strip()
        categories = [
            category.get("term", "")
            for category in element.findall("atom:category", ATOM_NS)
        ]
        authors = [
            (author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
            for author in element.findall("atom:author", ATOM_NS)
        ]
        comment = (
            element.findtext("arxiv:comment", default="", namespaces=ATOM_NS) or ""
        ).strip()
        entries.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "summary": summary,
                "published": published,
                "updated": updated,
                "url": url,
                "primary_category": primary,
                "categories": categories,
                "authors": authors,
                "comment": comment,
            }
        )
    return entries


def parse_atom_lenient(payload: str) -> list[dict[str, Any]]:
    """Parse an Atom payload; on truncation, salvage complete <entry> blocks."""
    try:
        return parse_atom(payload)
    except ET.ParseError:
        return _salvage_entries(payload)


def _salvage_entries(payload: str) -> list[dict[str, Any]]:
    pattern = re.compile(r"<entry>.*?</entry>", re.DOTALL)
    entries: list[dict[str, Any]] = []
    for block in pattern.findall(payload):
        wrapped = (
            '<feed xmlns="http://www.w3.org/2005/Atom" '
            'xmlns:arxiv="http://arxiv.org/schemas/atom">' + block + "</feed>"
        )
        try:
            entries.extend(parse_atom(wrapped))
        except ET.ParseError:
            continue
    return entries


def _request_payload(url: str) -> tuple[str, bool]:
    """Return (payload, complete). Complete is False when the stream was cut."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        try:
            return response.read().decode("utf-8", errors="replace"), True
        except http.client.IncompleteRead as exc:
            partial = getattr(exc, "partial", b"") or b""
            return partial.decode("utf-8", errors="replace"), False


def fetch_entries(
    query: str,
    max_results: int = 20,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
    start: int = 0,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    key = json.dumps(
        [query, max_results, sort_by, sort_order, start], ensure_ascii=False, sort_keys=True
    )
    if use_cache:
        cached = _load_cache(key)
        if cached is not None:
            return cached

    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit()
            payload, complete = _request_payload(url)
            entries = parse_atom_lenient(payload)
            if complete or entries:
                if not complete:
                    print(
                        f"[arxiv] truncated response salvaged: {len(entries)} "
                        "entries recovered from partial payload"
                    )
                _save_cache(key, entries)
                return entries
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            http.client.HTTPException,
        ) as exc:
            last_error = exc
            if attempt + 1 < MAX_RETRIES:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"arXiv fetch failed after {MAX_RETRIES} attempts: {last_error}")


def search_recent(
    categories: list[str],
    max_results: int = 40,
    days_back: int = 14,
    until_days_back: int | None = None,
    terms: str | None = None,
    sort_by: str = "submittedDate",
) -> list[dict[str, Any]]:
    """Fetch papers in the window [now-days_back, now-until_days_back).

    When until_days_back is None the window reaches "now"; otherwise windows
    can be made non-overlapping for historical backfills.
    """
    now = datetime.now(UTC)
    window_start = now - timedelta(days=days_back)
    window_end = now - timedelta(days=until_days_back) if until_days_back else now
    window = f"[{window_start:%Y%m%d%H%M} TO {window_end:%Y%m%d%H%M}]"
    clauses = [f"submittedDate:{window}"]
    if terms:
        clauses.append(f"({terms})")
    if categories:
        cat_clause = " OR ".join(f"cat:{category}" for category in categories)
        clauses.append(f"({cat_clause})")
    query = " AND ".join(clauses)
    return fetch_entries(query, max_results=max_results, sort_by=sort_by, sort_order="descending")

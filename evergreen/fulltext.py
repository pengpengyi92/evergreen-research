"""ar5iv full-text retrieval (stdlib-only).

ar5iv (ar5iv.labs.arxiv.org) serves LaTeX papers as HTML5 — parseable with
the stdlib HTMLParser, no PDF dependencies. Cached 7 days, retried, and
rate-limited politely.

Environment override for the cache dir (used by tests):
    EVERGREEN_AR5IV_CACHE=<path>
"""

from __future__ import annotations

import hashlib
import html as html_module
import http.client
import os
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

AR5IV_URL = "https://ar5iv.labs.arxiv.org/html"
ARXIV_HTML_URL = "https://arxiv.org/html"
USER_AGENT = "evergreen-research/0.2 (open-source frontier-AI research; stdlib client)"
REQUEST_GAP_SECONDS = 1.5
CACHE_TTL_SECONDS = 7 * 24 * 3600
MAX_RETRIES = 3

_last_request_ts = 0.0

_TAG_IGNORE = {"script", "style", "nav", "noscript", "svg", "math", "annotation"}


def _cache_root() -> Path:
    override = os.environ.get("EVERGREEN_AR5IV_CACHE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / ".cache" / "ar5iv"


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return _cache_root() / f"{digest}.html"


def normalize_arxiv_id(arxiv_id: str) -> str:
    """'http://arxiv.org/abs/2501.12948v3' -> '2501.12948'."""
    base = arxiv_id.split("/abs/")[-1]
    base = re.sub(r"v\d+$", "", base)
    return base


def _rate_limit() -> None:
    global _last_request_ts
    elapsed = time.monotonic() - _last_request_ts
    if _last_request_ts and elapsed < REQUEST_GAP_SECONDS:
        time.sleep(REQUEST_GAP_SECONDS - elapsed)
    _last_request_ts = time.monotonic()


def _cache_payload(normalized: str, payload: str) -> None:
    try:
        path = _cache_path(normalized)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    except OSError:
        pass


MIN_USABLE_PARTIAL_BYTES = 50_000


def _looks_like_paper_html(payload: str) -> bool:
    """Real LaTeXML pages carry ltx_ markers; arXiv abs-page fallbacks do not."""
    return "ltx_" in payload or "LaTeXML" in payload


def _fetch_url(url: str, normalized: str) -> str | None:
    """Fetch one URL with retries and partial-response salvage."""
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit()
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=45) as response:
                try:
                    payload = response.read().decode("utf-8", errors="replace")
                except http.client.IncompleteRead as exc:
                    partial = getattr(exc, "partial", b"") or b""
                    payload = partial.decode("utf-8", errors="replace")
                    if len(payload) < MIN_USABLE_PARTIAL_BYTES:
                        if "Skip to main content" in payload:
                            # Truncated arXiv abs-page fallback: no fulltext here.
                            return None
                        raise
            _cache_payload(normalized, payload)
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            last_error = exc
            if attempt + 1 < MAX_RETRIES:
                time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, http.client.HTTPException) as exc:
            last_error = exc
            if attempt + 1 < MAX_RETRIES:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"fulltext fetch failed after {MAX_RETRIES} attempts: {last_error}")


def fetch_ar5iv(arxiv_id: str, use_cache: bool = True) -> str | None:
    """Fetch the ar5iv HTML for an arXiv id; None when unavailable (404)."""
    normalized = normalize_arxiv_id(arxiv_id)
    if use_cache:
        path = _cache_path(normalized)
        if path.exists():
            try:
                age = time.time() - path.stat().st_mtime
                if age < CACHE_TTL_SECONDS:
                    return path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    return _fetch_url(f"{AR5IV_URL}/{normalized}", normalized)


def fetch_arxiv_html(arxiv_id: str, use_cache: bool = True) -> str | None:
    """Fetch arXiv's native HTML rendering (covers papers ar5iv lacks)."""
    normalized = normalize_arxiv_id(arxiv_id)
    if use_cache:
        path = _cache_path("arxiv-" + normalized)
        if path.exists():
            try:
                age = time.time() - path.stat().st_mtime
                if age < CACHE_TTL_SECONDS:
                    return path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    return _fetch_url(f"{ARXIV_HTML_URL}/{normalized}", "arxiv-" + normalized)


def fetch_fulltext(arxiv_id: str) -> tuple[str | None, str]:
    """Return (html, source) for the best available full-text rendering.

    Order: ar5iv first (best LaTeXML quality), then arXiv native HTML for
    papers ar5iv has not converted yet. Rejects arXiv abs-page fallbacks
    masquerading as paper HTML.
    """
    html_payload = fetch_ar5iv(arxiv_id)
    if html_payload and _looks_like_paper_html(html_payload):
        return html_payload, "ar5iv"
    html_payload = fetch_arxiv_html(arxiv_id)
    if html_payload and _looks_like_paper_html(html_payload):
        return html_payload, "arxiv-html"
    return None, "unavailable"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._depth_ignore = 0
        self._capture = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _TAG_IGNORE:
            self._depth_ignore += 1
            return
        if self._depth_ignore:
            return
        if tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "blockquote", "figcaption", "div"}:
            self._capture = True
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _TAG_IGNORE and self._depth_ignore:
            self._depth_ignore -= 1
            return
        if tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "blockquote", "figcaption", "div"}:
            self._capture = False
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._depth_ignore or not self._capture:
            return
        self.parts.append(data)


def html_to_text(html_payload: str) -> str:
    """Deterministically extract readable text from ar5iv HTML."""
    extractor = _TextExtractor()
    try:
        extractor.feed(html_payload)
    except Exception:
        pass
    text = "".join(extractor.parts)
    text = html_module.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

"""GitHub org/user repo radar (keyless, stdlib-only).

Tracks the *development* side of a research group: each paper-repo is a
data point with stars (impact proxy), language, topics, and activity.
Unauthenticated GitHub API is 60 req/h — one weekly call per watchlist
entry is well within limits.

Environment override for the cache dir (used by tests):
    PRESEARCH_GH_CACHE=<path>
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

API_URL = "https://api.github.com"
USER_AGENT = "p-research/0.5 (open-source frontier-AI research; contact: pengpengyi92@gmail.com)"
CACHE_TTL_SECONDS = 24 * 3600
MAX_RETRIES = 3


def _cache_root() -> Path:
    override = os.environ.get("PRESEARCH_GH_CACHE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / ".cache" / "github"


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


def _save_cache(key: str, data: list[dict[str, Any]]) -> None:
    try:
        path = _cache_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def org_repos(org: str, per_page: int = 100, use_cache: bool = True) -> list[dict[str, Any]]:
    """List an org's public repos sorted by push activity."""
    key = f"org-{org.lower()}-{per_page}"
    if use_cache:
        cached = _load_cache(key)
        if cached is not None:
            return cached
    params = {"per_page": per_page, "sort": "pushed"}
    url = f"{API_URL}/orgs/{urllib.parse.quote(org)}/repos?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"Bearer {token}"
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            repos = [
                {
                    "name": repo.get("name", ""),
                    "full_name": repo.get("full_name", ""),
                    "description": repo.get("description") or "",
                    "language": repo.get("language") or "",
                    "stars": repo.get("stargazers_count") or 0,
                    "forks": repo.get("forks_count") or 0,
                    "topics": repo.get("topics") or [],
                    "pushed_at": repo.get("pushed_at") or "",
                    "html_url": repo.get("html_url") or "",
                }
                for repo in payload
            ]
            _save_cache(key, repos)
            return repos
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, http.client.HTTPException) as exc:
            last_error = exc
            if attempt + 1 < MAX_RETRIES:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GitHub org fetch failed after {MAX_RETRIES} attempts: {last_error}")


_PILLAR_KEYWORDS: dict[str, list[str]] = {
    "LLM Reasoning / Test-time Compute": ["reasoning", "chain-of-thought", "verifier", "reward", "think"],
    "Agentic AI / Deep Research Systems": ["agent", "multi-agent", "tool", "browser", "computer", "swarm", "tutor", "coworker", "research", "deepcode", "harness", "skill"],
    "Efficient Training & Inference": ["quantiz", "moe", "distill", "long-context", "long context", "kv cache", "pruning", "compression"],
    "RL / Alignment / Safety": ["alignment", "safety", "interpretab", "jailbreak", "guard"],
    "Multimodal / World Models": ["video", "vision", "image", "multimodal", "world model", "vlm", "music", "audio"],
    "Quant × AI": ["trading", "trader", "stock", "finance", "market", "portfolio", "quant", "money"],
    "Graph / RecSys (pre-LLM line)": ["graph", "recommend", "recsys", "collaborative", "sequential", "spatio", "contrastive"],
}

_VENUE_YEAR_RE = re.compile(r"\[?([A-Za-z]+['\u2019]?\d{2,4})\]?")


def classify_repos(repos: list[dict[str, Any]]) -> dict[str, Any]:
    """Map repos onto the six-pillar taxonomy (+ legacy bucket) and extract
    venue years from paper-repo descriptions."""
    from collections import Counter

    pillar_counter: Counter = Counter()
    year_counter: Counter = Counter()
    classified: list[dict[str, Any]] = []
    for repo in repos:
        text = " ".join(
            [repo.get("name", ""), repo.get("description", ""), " ".join(repo.get("topics", []))]
        ).lower()
        hit_counts = {
            pillar: sum(1 for keyword in keywords if keyword in text)
            for pillar, keywords in _PILLAR_KEYWORDS.items()
        }
        if any(hit_counts.values()):
            pillar = max(hit_counts, key=lambda name: hit_counts[name])
        else:
            pillar = "Other / Uncategorized"
        pillar_counter[pillar] += 1
        year = ""
        match = _VENUE_YEAR_RE.search(repo.get("description", ""))
        if match:
            raw = match.group(1)
            digits = re.sub(r"\D", "", raw)
            year = ("20" + digits[-2:]) if len(digits) == 2 and digits[-2:] >= "20" else digits[:4]
            if len(year) == 4:
                year_counter[year] += 1
        classified.append(
            {
                "name": repo["name"],
                "stars": repo["stars"],
                "pillar": pillar,
                "venue_year": year or "",
                "pushed": repo["pushed_at"][:10],
            }
        )
    return {
        "by_pillar": dict(pillar_counter.most_common()),
        "by_venue_year": dict(sorted(year_counter.items())),
        "classified": classified,
    }


def repos_report(repos: list[dict[str, Any]], org: str) -> dict[str, Any]:
    active = [repo for repo in repos if repo.get("pushed_at", "").startswith(("2025", "2026"))]
    return {
        "org": org,
        "total_repos": len(repos),
        "active_repos": len(active),
        "total_stars": sum(repo["stars"] for repo in repos),
        "languages": sorted({repo["language"] for repo in repos if repo.get("language")}),
        "top": sorted(repos, key=lambda repo: -repo["stars"])[:15],
    }

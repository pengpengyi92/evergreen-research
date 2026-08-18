"""RSS feed for the weekly frontier digests (stdlib-only)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any

CHANNEL_TITLE = "Evergreen Research — Frontier AI Weekly"
CHANNEL_LINK = "https://github.com/evergreen-research"  # updated after push
CHANNEL_DESCRIPTION = (
    "Weekly digests of the frontier-AI research corpus: arXiv sweeps, "
    "cross-pillar convergence signals, and survey progress."
)


def _item_description(markdown: str, limit: int = 400) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"[#>*`_]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def write_feed(data_root: Path, quiet: bool = False) -> Path:
    weekly_dir = data_root / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)

    channel = ET.Element("channel")
    ET.SubElement(channel, "title").text = CHANNEL_TITLE
    ET.SubElement(channel, "link").text = CHANNEL_LINK
    ET.SubElement(channel, "description").text = CHANNEL_DESCRIPTION

    digests = sorted(weekly_dir.glob("*.md"), reverse=True)
    for digest in digests[:12]:
        content = digest.read_text(encoding="utf-8")
        title = f"Frontier AI Weekly {digest.stem}"
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = f"{CHANNEL_LINK}/blob/main/data/weekly/{digest.name}"
        ET.SubElement(item, "guid").text = f"evergreen-weekly-{digest.stem}"
        published = datetime.now(timezone.utc)
        ET.SubElement(item, "pubDate").text = format_datetime(published)
        ET.SubElement(item, "description").text = _item_description(content)

    rss = ET.Element("rss", {"version": "2.0"})
    rss.append(channel)
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    path = weekly_dir / "feed.xml"
    tree.write(path, encoding="utf-8", xml_declaration=True)
    if not quiet:
        print(f"[rss] {len(digests)} digests -> {path}")
    return path

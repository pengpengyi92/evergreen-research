"""Checksummed snapshot archive of the public research data (Zenodo-ready).

`evergreen snapshot` packs data/ (papers.jsonl, citations, novelty, weekly,
survey) into data/snapshots/evergreen-data-<date>.tar.gz with a
SHA-256 manifest, fulfilling the §7.5 reproducibility promise.
"""

from __future__ import annotations

import hashlib
import tarfile
from datetime import date
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(data_root: Path, quiet: bool = False) -> dict[str, Any]:
    data_root = Path(data_root)
    today = date.today().isoformat()
    snapshot_dir = data_root / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    archive = snapshot_dir / f"evergreen-data-{today}.tar.gz"
    manifest_path = snapshot_dir / f"evergreen-data-{today}.sha256"

    files = sorted(data_root.rglob("*"))
    files = [
        path
        for path in files
        if path.is_file() and "snapshots" not in path.parts and "__pycache__" not in path.parts
    ]
    manifest_lines: list[str] = []
    with tarfile.open(archive, "w:gz") as tar:
        for path in files:
            tar.add(path, arcname=path.relative_to(data_root))
            manifest_lines.append(f"{_sha256(path)}  {path.relative_to(data_root)}")
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    if not quiet:
        print(f"[snapshot] {archive} ({len(files)} files, manifest {manifest_path})")
    return {
        "archive": str(archive),
        "manifest": str(manifest_path),
        "files": len(files),
        "archive_sha256": _sha256(archive),
    }

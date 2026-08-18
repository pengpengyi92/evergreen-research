# Changelog

## [0.2.0] - 2026-08-18

### Added

- Historical corpus backfill with non-overlapping date windows (`evergreen backfill`) — corpus grew to 500+ papers across 2023-2026.
- Full-text verification (`evergreen verify`): ar5iv-first with arXiv native HTML fallback, abs-page rejection, partial-response salvage, and `verified` metadata on database records.
- Survey outline v0.2: 7-section compute-allocation structure + inclusion criteria.
- Database record updates (atomic rewrite) for verification metadata.

## [0.1.0] - 2026-08-18

### Added

- Weekly frontier-AI pipeline: six-pillar arXiv sweep -> deterministic
  structuring -> append-only JSONL database -> cross-pillar clustering ->
  weekly digest + index + survey outline.
- `evergreen` CLI: `weekly`, `fetch`, `db stats`, `survey`.
- Rate-limited arXiv client with retries and truncated-response salvage.
- GitHub Actions weekly cron with auto-commit.
- Offline unit tests (25 in the internal suite; ported subset here).

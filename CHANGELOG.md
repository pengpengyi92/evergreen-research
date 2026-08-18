# Changelog

## [0.1.0] - 2026-08-18

### Added

- Weekly frontier-AI pipeline: six-pillar arXiv sweep -> deterministic
  structuring -> append-only JSONL database -> cross-pillar clustering ->
  weekly digest + index + survey outline.
- `evergreen` CLI: `weekly`, `fetch`, `db stats`, `survey`.
- Rate-limited arXiv client with retries and truncated-response salvage.
- GitHub Actions weekly cron with auto-commit.
- Offline unit tests (25 in the internal suite; ported subset here).

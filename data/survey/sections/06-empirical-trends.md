# §6 Empirical Trends from the Living Corpus

> Draft v0.1. All numbers are corpus statements, regenerated from
> `data/papers.jsonl` on every sweep. Verified subsets are preferred where
> available; abstract-level counts are labeled as such.

## 6.1 Method migration: the RLVR wave (verified)

Full-text-verified records show the sharpest single trend in the corpus:
RLVR/GRPO quadrupled from 4 (2024) to 18 (2025) verified papers, with 6
already in the partial year 2026; preference-optimization language grew
3 → 20 → 7. Chain-of-thought (2 → 12 → 4) grew more slowly, consistent
with the §3 reading that CoT is being absorbed as a *substrate* of learned
reasoning rather than remaining a prompting technique.

Abstract-level counts across all six pillars tell the same story with more
noise (RLVR: 17/18/21/14 over 2023-2026) — the 2023 elevation is a
backfill-window artifact (§6.4).

## 6.2 Benchmark concentration — and where the hard ones hide

In verified lead-pillar full texts, three benchmarks dominate: MATH (13),
DROP (12), GSM8K (8). High-difficulty suites (AIME: 2, MMLU: 2) appear far
less often — but note the *location* asymmetry: AIME/GPQA almost never
appear in abstracts, while MATH/GSM8K do. Abstract-level benchmark mining
therefore systematically under-counts hard benchmarks; full-text
verification corrects it. For survey purposes this matters: a reader
judging "reasoning progress" from abstracts alone will see an easier field
than the papers actually evaluate on.

## 6.3 The frontier moves weekly

The weekly digests (`data/weekly/`) archive the moving frontier. The
2026-W34 sweep (the first) ingested 69 papers across the six pillars with
zero degraded queries; convergence signals that week included VLM spanning
4 pillars (12 papers) and preference optimization spanning 4 (10 papers).
Each digest carries the sweep's convergence signals and degraded-pillar
log, so trend claims in this survey can be audited week by week.

## 6.4 Corpus-construction biases (reported, not hidden)

1. **Window weighting.** Weekly sweeps cover the last 21 days; backfills
   cover fixed windows (0-360, 360-720, 720-1080, 1080-2160 days). Recent
   years are over-represented; 2026 is partial.
2. **Query-of-origin pillar assignment.** A paper's pillar follows the
   query that found it, not a content classifier. Cross-pillar counts
   measure query overlap plus true migration (§5.6).
3. **Abstract-level noise.** Keyword tags overstate co-occurrence; only
   full-text-verified records (45, method match rate 99%) back hard claims.
4. **arXiv-only.** Closed-model reports, non-English venues, and
   non-arXiv publications are out of scope (§1.5).

## 6.5 What §6 contributes

- A *method-migration* estimate with verified backing (RLVR 4→18).
- A *benchmark-visibility asymmetry* (hard benchmarks hide in full text).
- An *auditable cadence* — every trend links to weekly digests and DB
  records, so the survey's numbers can be re-derived, not just re-cited.

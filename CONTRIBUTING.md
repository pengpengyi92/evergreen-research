# Contributing to P-Research

## Ways to contribute

1. **Review a weekly digest** (highest value). Open an issue titled
   `review: 2026-W34 <pillar>` and challenge a claim, fix a tag, or verify a
   paper by reading its full text. Cite the paper record id from
   `data/papers.jsonl`.
2. **Improve the structurer**. The keyword tables and regexes live in
   `presearch/structurer.py`. Add a method/benchmark/model entry with a test
   in `tests/`.
3. **Add a pillar or a query**. Pillars live in `presearch/pillars.py`.
4. **Fix the pipeline**. Everything is deterministic and unit-tested.

## Development

```bash
python3 -m unittest discover -s tests
python3 -m presearch.cli weekly --max-per-pillar 3   # small smoke sweep
```

## Conventions

- stdlib-only Python (>= 3.10). No runtime dependencies.
- Every claim in a digest must be traceable to a `data/papers.jsonl` record.
- Metadata is a research signal, not a fact: keep the disclaimer in place.
- Conventional commits for the auto-bot (`chore(weekly): ...`).

## Review gate

PRs that change survey claims (`data/survey/`) require at least one reviewer
who has read the relevant papers' abstracts (and ideally full texts).

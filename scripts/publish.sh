#!/usr/bin/env bash
# First-time publish for evergreen-research.
# Run AFTER `gh auth login`. Then follow the LAUNCH.md steps for Pages.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! gh auth status >/dev/null 2>&1; then
  echo "gh not authenticated. Run: gh auth login -h github.com" >&2
  exit 1
fi

echo "== creating public repo =="
gh repo create evergreen-research --public --source=. --push \
  --description "Self-updating frontier-AI research intelligence: weekly arXiv sweeps, a living paper database (500+ papers), full-text verification, and a growing survey." \
  --homepage "https://github.com/$(gh api user --jq .login)/evergreen-research"

echo "== setting topics =="
gh repo edit --add-topic arxiv --add-topic deep-research \
  --add-topic research-intelligence --add-topic survey --add-topic frontier-ai

echo "== next manual step =="
echo "Settings -> Pages -> Source: Deploy from a branch -> main /docs -> Save"
echo "Then: Actions -> weekly-research -> Run workflow (first manual run)"

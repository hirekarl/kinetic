#!/usr/bin/env bash
# Kinetic Release Ceremony
# Aggregates conventional commits → calculates SemVer bump →
# updates CHANGELOG.md → creates release commit + tag.
#
# Usage: ./scripts/release.sh [--increment MAJOR|MINOR|PATCH]
#
# Requires: uv, commitizen (installed via uv sync --group dev)

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

info()    { echo -e "${BOLD}[release]${RESET} $*"; }
success() { echo -e "${GREEN}✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET} $*"; }
fail()    { echo -e "${RED}✗${RESET} $*"; exit 1; }

# ── Parse args ─────────────────────────────────────────────────────────────

INCREMENT_FLAG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --increment)
      INCREMENT_FLAG="--increment $2"
      shift 2
      ;;
    *) fail "Unknown argument: $1" ;;
  esac
done

# ── Preflight ──────────────────────────────────────────────────────────────

info "Running preflight checks..."

command -v uv >/dev/null 2>&1 || fail "uv not found. Install from https://docs.astral.sh/uv/"

if ! git diff --quiet || ! git diff --cached --quiet; then
  fail "Working tree is dirty. Commit or stash changes before releasing."
fi

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
info "Last release tag: ${LAST_TAG}"

# ── Commit validation ──────────────────────────────────────────────────────

info "Validating conventional commits since ${LAST_TAG}..."

if [ "$LAST_TAG" = "none" ]; then
  uv run cz check --rev-range HEAD || fail "Commit messages violate Conventional Commits spec."
else
  uv run cz check --rev-range "${LAST_TAG}..HEAD" || fail "Commit messages violate Conventional Commits spec."
fi
success "All commits are valid."

# ── Preview ────────────────────────────────────────────────────────────────

echo ""
info "Version bump preview:"
uv run cz bump --dry-run $INCREMENT_FLAG

echo ""
info "Changelog preview:"
uv run cz changelog --dry-run

# ── Confirm ────────────────────────────────────────────────────────────────

echo ""
read -r -p "$(echo -e "${BOLD}Proceed with release?${RESET} [y/N] ")" confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { warn "Release aborted."; exit 0; }

# ── Bump + tag ─────────────────────────────────────────────────────────────

info "Bumping version, updating CHANGELOG, creating release commit + tag..."
uv run cz bump --changelog $INCREMENT_FLAG
success "Version bumped and tagged."

# ── Push ───────────────────────────────────────────────────────────────────

echo ""
info "Ready to push:"
git log --oneline -3

echo ""
read -r -p "$(echo -e "${BOLD}Push commit and tag to origin?${RESET} [y/N] ")" push_confirm
if [[ "$push_confirm" =~ ^[Yy]$ ]]; then
  git push && git push --tags
  success "Release pushed. 🚀"
else
  warn "Push skipped. Run 'git push && git push --tags' when ready."
fi

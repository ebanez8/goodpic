#!/usr/bin/env bash
set -euo pipefail
project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$project/external/inksight"
[[ -f "$repo/uv.lock" ]] || { echo "Clone https://github.com/google-research/inksight to $repo first." >&2; exit 1; }
command -v uv >/dev/null || { echo 'Install uv: https://docs.astral.sh/uv/' >&2; exit 1; }
(cd "$repo" && uv sync --locked)

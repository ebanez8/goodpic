#!/usr/bin/env bash
set -euo pipefail
project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${PYTHON_BIN:-python3.11}"
if [[ ! -x "$project/.venv/bin/python" ]]; then
  "$python_bin" -m venv "$project/.venv"
fi
"$project/.venv/bin/python" -m pip install -e "$project[dev]"
"$project/.venv/bin/python" "$project/scripts/check_environment.py"

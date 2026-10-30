#!/usr/bin/env bash
# Install from PyPI. If testzeus-sdk>=0.0.28 is unpublished, use the latest
# published SDK so lint/build can run on this public repository.
set -euo pipefail

set +e
uv sync --dev
status=$?
set -e
if [ "$status" -eq 0 ]; then
  echo "Installed dependencies from package indexes"
  exit 0
fi

echo "testzeus-sdk>=0.0.28 is not on PyPI yet; using the latest published SDK for lint/build"
python3 - <<'PY'
from pathlib import Path

path = Path("pyproject.toml")
text = path.read_text()
old = '"testzeus-sdk>=0.0.28,!=0.0.26"'
new = '"testzeus-sdk>=0.0.27,!=0.0.26"'
if old not in text:
    raise SystemExit("could not rewrite the testzeus-sdk pin in pyproject.toml")
path.write_text(text.replace(old, new, 1))
PY

uv lock --upgrade-package testzeus-sdk
uv sync --dev

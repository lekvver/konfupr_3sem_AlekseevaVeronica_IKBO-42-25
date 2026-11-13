#!/usr/bin/env bash
# Запуск инструмента: ./run.sh -p PACKAGE -r REPO [-t] [-o FILE]
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${root}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec python3 -m depgraph "$@"

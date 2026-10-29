#!/usr/bin/env bash
# Запуск эмулятора: ./run.sh
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${root}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec python3 -m shell_emulator "$@"

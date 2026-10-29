#!/usr/bin/env bash
# Этап 2: запуск эмулятора без параметров командной строки.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

show_case "без параметров: оба параметра выводятся как не заданные"
# shellcheck disable=SC2119
run_emulator
expect_status 0
expect_output '[debug]   vfs    = <not set>'
expect_output '[debug]   script = <not set>'
expect_output 'exit'

finish

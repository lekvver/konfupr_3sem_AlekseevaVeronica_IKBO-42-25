#!/usr/bin/env bash
# Этап 2: неверные параметры командной строки и справка.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

show_case "неизвестный параметр: сообщение об ошибке, код 2"
run_emulator --bogus
expect_status 2
expect_output 'usage: shell_emulator'
expect_output 'unrecognized arguments'

show_case "параметр --vfs без значения: код 2"
run_emulator --vfs
expect_status 2
expect_output 'usage: shell_emulator'

show_case "--help: справка, код 0"
run_emulator --help
expect_status 0
expect_output '--vfs PATH'
expect_output '--script PATH'

finish

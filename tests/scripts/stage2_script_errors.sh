#!/usr/bin/env bash
# Этап 2: ошибки при выполнении стартового скрипта.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

script="${STARTUP_DIR}/with_errors.emu"

show_case "ошибочные строки пропускаются, об ошибках сообщается"
run_emulator --script "${script}"
expect_status 7
expect_output 'with_errors.emu: line 3: unknown_command: command not found'
expect_output 'with_errors.emu: line 4: syntax error'
expect_output 'with_errors.emu: line 6: exit: too many arguments'
expect_output "ls: args=['first']"
expect_output "cd: args=['second']"
expect_output "ls: args=['third']"
reject_output 'never-executed'

show_case "скрипт не найден: сообщение об ошибке и код 1"
run_emulator --script "${TMP_DIR}/missing.emu"
expect_status 1
expect_output 'cannot read startup script'
expect_output 'No such file or directory'

show_case "вместо скрипта указан каталог: сообщение об ошибке и код 1"
run_emulator --script "${TMP_DIR}"
expect_status 1
expect_output 'cannot read startup script'
expect_output 'Is a directory'

finish

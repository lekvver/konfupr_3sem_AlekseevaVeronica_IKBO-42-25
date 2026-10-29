#!/usr/bin/env bash
# Этап 2: параметр --script (путь к стартовому скрипту).
# shellcheck disable=SC2016
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

script="${STARTUP_DIR}/basic.emu"

show_case "--script ПУТЬ: на экране и ввод, и вывод скрипта"
run_emulator --script "${script}"
expect_status 0
expect_output "[debug]   script = ${script}"
expect_output '[debug]   vfs    = <not set>'
expect_output '$ ls -l /tmp'
expect_output "ls: args=['-l', '/tmp']"
expect_output '$ cd $HOME'
expect_output "cd: args=['${HOME}']"
expect_output "cd: args=['\$HOME']"
expect_output '$ exit'

finish

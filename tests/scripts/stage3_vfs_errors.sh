#!/usr/bin/env bash
# Этап 3: ошибки загрузки VFS (нет каталога, неверный формат).
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

script="${STARTUP_DIR}/basic.emu"

show_case "каталог VFS не найден: ошибка, код 1, скрипт не запускается"
run_emulator --vfs "${TMP_DIR}/nope" --script "${script}"
expect_status 1
expect_output "error: VFS not found: ${TMP_DIR}/nope"
reject_output 'ls: args'

show_case "вместо каталога указан файл: неверный формат"
file="${TESTS_DIR}/vfs/minimal/hello.txt"
run_emulator --vfs "${file}" --script "${script}"
expect_status 1
expect_output "error: invalid VFS format: not a directory: ${file}"
reject_output 'ls: args'

show_case "символическая ссылка внутри VFS: неверный формат"
bad="${TMP_DIR}/with_link"
mkdir "${bad}"
ln -s hello.txt "${bad}/link"
run_emulator --vfs "${bad}" --script "${script}"
expect_status 1
expect_output 'invalid VFS format: symbolic link is not supported'

finish

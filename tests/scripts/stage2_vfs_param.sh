#!/usr/bin/env bash
# Этап 2: параметр --vfs (путь к физическому расположению VFS).
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

vfs_dir="${TMP_DIR}/vfs"
mkdir "${vfs_dir}"

show_case "--vfs ПУТЬ: путь попадает в отладочный вывод"
run_emulator --vfs "${vfs_dir}"
expect_status 0
expect_output "[debug]   vfs    = ${vfs_dir}"
expect_output '[debug]   script = <not set>'

show_case "--vfs=ПУТЬ: запись через знак равенства"
run_emulator "--vfs=${vfs_dir}"
expect_status 0
expect_output "[debug]   vfs    = ${vfs_dir}"

finish

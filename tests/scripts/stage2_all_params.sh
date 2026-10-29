#!/usr/bin/env bash
# Этап 2: оба параметра командной строки одновременно.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

vfs_dir="${TMP_DIR}/vfs"
mkdir "${vfs_dir}"
script="${STARTUP_DIR}/basic.emu"

show_case "--vfs и --script вместе"
run_emulator --vfs "${vfs_dir}" --script "${script}"
expect_status 0
expect_output "[debug]   vfs    = ${vfs_dir}"
expect_output "[debug]   script = ${script}"
expect_output "ls: args=['-l', '/tmp']"

show_case "те же параметры в другом порядке"
run_emulator --script "${script}" --vfs "${vfs_dir}"
expect_status 0
expect_output "[debug]   vfs    = ${vfs_dir}"
expect_output "[debug]   script = ${script}"

finish

#!/usr/bin/env bash
# Этап 3: путь к VFS не указан, VFS по умолчанию создаётся в памяти.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

export VFS_OUT="${TMP_DIR}/out_default"

show_case "без --vfs: создаётся VFS по умолчанию"
run_emulator --script "${STARTUP_DIR}/save_vfs.emu"
expect_status 0
expect_output '[info] no VFS path given, default in-memory VFS created'
expect_output '4 directories, 1 files'
expect_output "VFS saved to ${VFS_OUT}"
expect_file "${VFS_OUT}/etc/motd"
expect_dir "${VFS_OUT}/home/user"
expect_dir "${VFS_OUT}/tmp"

finish

#!/usr/bin/env bash
# Этап 3: VFS с несколькими файлами в одном каталоге.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

vfs="${TESTS_DIR}/vfs/several_files"
export VFS_OUT="${TMP_DIR}/out_files"

show_case "несколько файлов: загрузка и сохранение"
run_emulator --vfs "${vfs}" --script "${STARTUP_DIR}/save_vfs.emu"
expect_status 0
expect_output "[info] VFS loaded from ${vfs}: 0 directories, 5 files"
expect_output "VFS saved to ${VFS_OUT}"
expect_file "${VFS_OUT}/readme.txt"
expect_file "${VFS_OUT}/data.csv"
expect_same_tree "${vfs}" "${VFS_OUT}"

finish

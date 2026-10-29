#!/usr/bin/env bash
# Этап 3: минимальные варианты VFS (один файл и пустой каталог).
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

save_script="${STARTUP_DIR}/save_vfs.emu"

vfs="${TESTS_DIR}/vfs/minimal"
export VFS_OUT="${TMP_DIR}/out_minimal"
show_case "минимальная VFS: один файл, загрузка и сохранение"
run_emulator --vfs "${vfs}" --script "${save_script}"
expect_status 0
expect_output "[info] VFS loaded from ${vfs}: 0 directories, 1 files"
expect_output "VFS saved to ${VFS_OUT}"
expect_same_tree "${vfs}" "${VFS_OUT}"

vfs="${TMP_DIR}/empty"
mkdir "${vfs}"
export VFS_OUT="${TMP_DIR}/out_empty"
show_case "пустой каталог: корректная пустая VFS"
run_emulator --vfs "${vfs}" --script "${save_script}"
expect_status 0
expect_output "[info] VFS loaded from ${vfs}: 0 directories, 0 files"
expect_dir "${VFS_OUT}"
expect_same_tree "${vfs}" "${VFS_OUT}"

finish

#!/usr/bin/env bash
# Этап 3: VFS с глубокой вложенностью (больше трёх уровней).
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

vfs="${TESTS_DIR}/vfs/deep"
export VFS_OUT="${TMP_DIR}/out_deep"

show_case "вложенные каталоги: загрузка и сохранение"
run_emulator --vfs "${vfs}" --script "${STARTUP_DIR}/save_vfs.emu"
expect_status 0
expect_output "[info] VFS loaded from ${vfs}: 5 directories, 6 files"
expect_output "VFS saved to ${VFS_OUT}"
expect_file "${VFS_OUT}/README.txt"
expect_file "${VFS_OUT}/docs/manual/advanced/tuning.txt"
expect_file "${VFS_OUT}/src/lib/util.txt"
expect_same_tree "${vfs}" "${VFS_OUT}"

show_case "исходный каталог после работы не изменился"
run_emulator --vfs "${vfs}" --script "${STARTUP_DIR}/basic.emu"
expect_status 0
expect_same_tree "${vfs}" "${VFS_OUT}"

finish

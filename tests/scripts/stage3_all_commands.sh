#!/usr/bin/env bash
# Этап 3: стартовый скрипт со всеми командами этапов 1-3,
# включая работу с VFS и обработку ошибок.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

export VFS_SRC="${TESTS_DIR}/vfs/deep"
export VFS_OUT="${TMP_DIR}/saved"
export VFS_FILE="${TMP_DIR}/file.txt"
: > "${VFS_FILE}"

show_case "all_commands.emu на VFS с глубокой вложенностью"
run_emulator --vfs "${VFS_SRC}" --script "${STARTUP_DIR}/all_commands.emu"
expect_status 3

expect_output "ls: args=['-l', '/tmp']"
expect_output "cd: args=['..']"
expect_output "cd: args=['${HOME}']"
expect_output "cd: args=['${HOME}/projects']"
expect_output "cd: args=['${HOME}/my docs']"
expect_output "cd: args=['\$HOME']"
expect_output "ls: args=['done']"
expect_output "ls: args=['two words', 'single \$quoted', '']"

expect_output 'frobnicate: command not found'
expect_output 'syntax error: unexpected end of line'

expect_output "VFS saved to ${VFS_OUT}"
expect_output 'vfs-save: missing path operand'
expect_output 'vfs-save: too many arguments'
expect_output "directory ${VFS_OUT} is not empty"
expect_output "${VFS_FILE} already exists and is not a directory"
expect_output "${VFS_SRC} is the source directory or inside it"
expect_output 'exit: too many arguments'
expect_same_tree "${VFS_SRC}" "${VFS_OUT}"

finish

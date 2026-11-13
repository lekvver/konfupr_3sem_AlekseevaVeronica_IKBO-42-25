#!/usr/bin/env bash
# Этап 1: вывод параметров и обработка ошибок для каждого параметра.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

URL="http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/"
LOCAL="file://${TESTS_DIR}/data/index"
printf 'A: B\nB:\n' > "${TMP_DIR}/repo.txt"

show_case "все параметры заданы: вывод ключ = значение"
run_tool -p base -r "${LOCAL}" -o "${TMP_DIR}/g.svg" --print-params
expect_status 0
expect_output "package   = base"
expect_output "test_mode = false"
expect_output "output    = ${TMP_DIR}/g.svg"

show_case "тестовый режим: --repo задаёт путь к файлу"
run_tool -p A -r "${TMP_DIR}/repo.txt" --test-mode --print-params
expect_output "test_mode = true"
expect_output "output    = graph.svg"

show_case "имя пакета: заглавные буквы в реальном режиме"
run_tool -p Bash -r "${URL}"
expect_status 2
expect_output "invalid package name"

show_case "имя пакета: строчные буквы в тестовом режиме"
run_tool -p a -r "${TMP_DIR}/repo.txt" -t
expect_status 2
expect_output "uppercase Latin letters"

show_case "имя пакета не задано"
run_tool -r "${URL}"
expect_status 2
expect_output "required"

show_case "репозиторий: путь вместо URL"
run_tool -p bash -r /etc/passwd
expect_status 2
expect_output "invalid repository URL"

show_case "репозиторий: URL без хоста"
run_tool -p bash -r http://
expect_status 2
expect_output "no host"

show_case "тестовый репозиторий: файл не найден"
run_tool -p A -r "${TMP_DIR}/missing.txt" -t
expect_status 2
expect_output "not found"

show_case "тестовый репозиторий: вместо файла каталог"
run_tool -p A -r "${TMP_DIR}" -t
expect_status 2
expect_output "is a directory"

show_case "выходной файл: неверное расширение"
run_tool -p bash -r "${URL}" -o graph.png
expect_status 2
expect_output ".svg"

show_case "выходной файл: каталог не существует"
run_tool -p bash -r "${URL}" -o /no/such/dir/graph.svg
expect_status 2
expect_output "does not exist"

show_case "неизвестный параметр и параметр без значения"
run_tool -p bash -r "${URL}" --bogus
expect_status 2
run_tool -p bash -r
expect_status 2

finish

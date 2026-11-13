#!/usr/bin/env bash
# Этап 2: прямые зависимости из индекса Packages (режим --direct).
# Часть 1 работает без сети (локальный индекс file://), часть 2 —
# с реальным репозиторием Ubuntu и пропускается, если сети нет.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

LOCAL="file://${TESTS_DIR}/data/index"
NOBLE="http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/"

show_case "локальный индекс: зависимости пакета app"
run_tool -p app -r "${LOCAL}" --direct
expect_status 0
expect_output "Direct dependencies of app 1.0-1 (5):"
expect_output "libbaz (one of: libbar | libbaz)"
expect_output "mta-one"

show_case "локальный индекс: пакет без зависимостей"
run_tool -p base -r "${LOCAL}" --direct
expect_status 0
expect_output "(none)"

show_case "локальный индекс: пакета нет"
run_tool -p nothing -r "${LOCAL}" --direct
expect_status 1
expect_output "not found in repository"

show_case "индекс не найден"
run_tool -p app -r "file://${TMP_DIR}" --direct
expect_status 1
expect_output "package index not found"

if curl -sfI -m 10 "${NOBLE}Packages.gz" > /dev/null; then
    show_case "реальный репозиторий Ubuntu noble/main: bash"
    run_tool -p bash -r "${NOBLE}" --direct
    expect_status 0
    expect_output "libc6"
    expect_output "base-files"

    show_case "реальный репозиторий: curl"
    run_tool -p curl -r "${NOBLE}" --direct
    expect_status 0
    expect_output "libcurl4t64"
else
    printf '\n(нет доступа к archive.ubuntu.com: реальный репозиторий пропущен)\n'
fi

finish

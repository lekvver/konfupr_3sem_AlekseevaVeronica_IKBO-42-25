#!/usr/bin/env bash
# Этап 3: граф зависимостей (BFS с рекурсией), циклы, тестовый режим.
# Текстовый вывод графа включается параметром --print-graph.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

run_repo() {
    # run_repo ФАЙЛ ПАКЕТ: запуск в тестовом режиме.
    run_tool -p "$2" -r "${REPOS_DIR}/$1" --test-mode --print-graph
}

show_case "цепочка A -> B -> C -> D (транзитивные зависимости)"
run_repo linear.txt A
expect_status 0
expect_output "4 packages, 3 edges"
expect_output "  C: D"
expect_output "No cyclic dependencies found"

show_case "дерево: уровни обхода в ширину"
run_repo tree.txt A
expect_status 0
expect_output "6 packages, 5 edges"

show_case "ромб: общая зависимость D учитывается один раз"
run_repo diamond.txt A
expect_status 0
expect_output "4 packages, 4 edges"

show_case "простой цикл A -> B -> C -> A"
run_repo cycle.txt A
expect_status 0
expect_output "A -> B -> C -> A"

show_case "зависимость пакета от самого себя"
run_repo self_loop.txt A
expect_status 0
expect_output "A -> A"

show_case "два цикла в одном графе"
run_repo two_cycles.txt A
expect_status 0
expect_output "Cyclic dependencies found (2):"
expect_output "A -> B -> A"
expect_output "B -> D -> B"

show_case "пакет Z нигде не описан: считается пакетом без зависимостей"
run_repo undefined.txt A
expect_status 0
expect_output "Z: (none)"

show_case "единственный пакет без зависимостей"
run_repo single.txt A
expect_status 0
expect_output "1 packages, 0 edges"

show_case "запятые, повторы и комментарии в файле"
run_repo syntax.txt A
expect_status 0
expect_output "  A: B, C"

show_case "сложный граф: недостижимые пакеты X и Y не попадают в граф"
run_repo complex.txt A
expect_status 0
expect_output "6 packages, 8 edges"
expect_output "B -> D -> F -> B"
reject_output "X:"

show_case "анализ другого пакета того же файла"
run_repo complex.txt X
expect_status 0
expect_output "2 packages, 1 edges"

show_case "ошибка: пакета нет в тестовом репозитории"
run_repo linear.txt Q
expect_status 1
expect_output "package 'Q' not found"

show_case "ошибки в файле тестового репозитория"
printf 'A: B\nB C\n' > "${TMP_DIR}/no_colon.txt"
run_tool -p A -r "${TMP_DIR}/no_colon.txt" -t --print-graph
expect_status 1
expect_output "line 2: expected"
printf 'A: b\n' > "${TMP_DIR}/lower.txt"
run_tool -p A -r "${TMP_DIR}/lower.txt" -t
expect_status 1
expect_output "invalid package name"
printf 'A: B\nA: C\n' > "${TMP_DIR}/twice.txt"
run_tool -p A -r "${TMP_DIR}/twice.txt" -t
expect_status 1
expect_output "defined twice"
: > "${TMP_DIR}/empty.txt"
run_tool -p A -r "${TMP_DIR}/empty.txt" -t
expect_status 1
expect_output "defines no packages"

show_case "режим --direct по-прежнему печатает только прямые зависимости"
run_tool -p A -r "${REPOS_DIR}/tree.txt" -t --direct
expect_status 0
expect_output "Direct dependencies of A (2):"

NOBLE="http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/"
if curl -sfI -m 10 "${NOBLE}Packages.gz" > /dev/null; then
    show_case "реальный репозиторий: libc6 (цикл libc6 <-> libgcc-s1)"
    run_tool -p libc6 -r "${NOBLE}" --print-graph
    expect_status 0
    expect_output "libc6 -> libgcc-s1 -> libc6"
else
    printf '\n(нет доступа к archive.ubuntu.com: реальный репозиторий пропущен)\n'
fi

finish

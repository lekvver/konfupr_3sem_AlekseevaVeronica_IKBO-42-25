#!/usr/bin/env bash
# Этап 4: порядок загрузки зависимостей (--load-order) на тестовых
# репозиториях и сравнение с настоящим apt.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

run_order() {
    # run_order ФАЙЛ ПАКЕТ: порядок загрузки в тестовом режиме.
    run_tool -p "$2" -r "${REPOS_DIR}/$1" --test-mode --load-order
}

show_case "цепочка: зависимости загружаются с конца"
run_order linear.txt A
expect_status 0
expect_output "  1. D"
expect_output "  4. A"

show_case "ромб: D один раз и до B и C"
run_order diamond.txt A
expect_status 0
expect_output "  1. D"
expect_output "  4. A"

show_case "дерево: порядок записи зависимостей сохраняется"
run_order tree.txt A
expect_status 0
expect_output "  1. D"
expect_output "  2. E"
expect_output "  3. B"
expect_output "  6. A"

show_case "цикл: обратное ребро пропускается"
run_order cycle.txt A
expect_status 0
expect_output "  1. C"
expect_output "Order inside cycles is arbitrary (1 found):"

show_case "два цикла и зависимость от самого себя"
run_order two_cycles.txt A
expect_status 0
expect_output "4 packages"
run_order self_loop.txt A
expect_status 0
expect_output "  1. B"

show_case "сложный граф: недостижимые X и Y в порядок не входят"
run_order complex.txt A
expect_status 0
expect_output "6 packages"
reject_output "X"

show_case "единственный пакет"
run_order single.txt A
expect_status 0
expect_output "  1. A"

show_case "ошибка: --direct и --load-order вместе"
run_tool -p A -r "${REPOS_DIR}/tree.txt" -t --direct --load-order
expect_status 2
expect_output "mutually exclusive"

NOBLE="http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/"
if curl -sfI -m 10 "${NOBLE}Packages.gz" > /dev/null \
    && command -v apt-get > /dev/null; then
    for package in nano bash dash; do
        show_case "сравнение с apt: ${package}"
        OUTPUT="$(bash "${SCRIPTS_DIR}/compare_apt.sh" "${package}" 2>&1)"
        printf '%s\n' "${OUTPUT}" | sed 's/^/    /'
        expect_output "Множества пакетов СОВПАДАЮТ"
    done
else
    printf '\n(нет сети или apt-get: сравнение с apt пропущено)\n'
fi

finish

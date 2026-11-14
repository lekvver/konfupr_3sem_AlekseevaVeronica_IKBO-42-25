#!/usr/bin/env bash
# Этап 5: текст D2 и SVG-изображение графа.
# Проверки SVG выполняются, если установлена программа d2; примеры с
# реальным репозиторием — если есть сеть.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

HAS_D2=0
command -v d2 > /dev/null && HAS_D2=1

expect_svg() {
    # Проверяет, что файл — SVG, и что в нём есть заданный пакет.
    expect_file "$1"
    if [ "${HAS_D2}" -eq 1 ]; then
        grep -q '<svg' "$1" || fail "not an SVG: $1"
        grep -q ">$2<" "$1" || fail "package $2 is not drawn in $1"
    fi
}

show_case "ромб: D2-текст и SVG"
run_tool -p A -r "${REPOS_DIR}/diamond.txt" -t -o "${TMP_DIR}/diamond.svg"
if [ "${HAS_D2}" -eq 1 ]; then
    expect_status 0
    expect_output "4 packages, 4 edges, 0 of them in cycles (red)"
    expect_svg "${TMP_DIR}/diamond.svg" D
fi
expect_file "${TMP_DIR}/diamond.d2"
grep -q '"B" -> "D"' "${TMP_DIR}/diamond.d2" || fail "no edge B -> D"
grep -q '"C" -> "D"' "${TMP_DIR}/diamond.d2" || fail "no edge C -> D"

show_case "цикл: рёбра цикла красные"
run_tool -p A -r "${REPOS_DIR}/cycle.txt" -t -o "${TMP_DIR}/cycle.svg"
grep -q '"C" -> "A": {style.stroke: "#d62728"}' "${TMP_DIR}/cycle.d2" \
    || fail "cycle edge is not highlighted"

show_case "сложный граф с двумя циклами"
run_tool -p A -r "${REPOS_DIR}/two_cycles.txt" -t -o "${TMP_DIR}/two.svg"
grep -q '"D" -> "B": {style.stroke' "${TMP_DIR}/two.d2" \
    || fail "cycle edge D -> B is not highlighted"

show_case "пакет без зависимостей"
run_tool -p A -r "${REPOS_DIR}/single.txt" -t -o "${TMP_DIR}/single.svg"
expect_file "${TMP_DIR}/single.d2"

show_case "нет программы d2: ошибка, но текст D2 сохранён"
DEPGRAPH_D2=/no/such/d2 run_tool -p A -r "${REPOS_DIR}/linear.txt" -t \
    -o "${TMP_DIR}/nod2.svg"
expect_status 1
expect_output "not found; install D2"
expect_file "${TMP_DIR}/nod2.d2"

show_case "ошибка: --print-graph вместе с --direct"
run_tool -p A -r "${REPOS_DIR}/linear.txt" -t --print-graph --direct
expect_status 2
expect_output "mutually exclusive"

NOBLE="http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/"
if curl -sfI -m 10 "${NOBLE}Packages.gz" > /dev/null; then
    for package in nano bash curl; do
        show_case "реальный репозиторий: ${package}"
        run_tool -p "${package}" -r "${NOBLE}" \
            -o "${TMP_DIR}/${package}.svg"
        expect_file "${TMP_DIR}/${package}.d2"
        if [ "${HAS_D2}" -eq 1 ]; then
            expect_status 0
            expect_svg "${TMP_DIR}/${package}.svg" "${package}"
            expect_svg "${TMP_DIR}/${package}.svg" libc6
        fi
    done
else
    printf '\n(нет доступа к archive.ubuntu.com: реальный репозиторий пропущен)\n'
fi

finish

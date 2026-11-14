#!/usr/bin/env bash
# Сравнение графа инструмента со штатными средствами apt (apt-cache).
# Использование: tests/scripts/compare_apt_graph.sh ПАКЕТ [СЬЮТ]
#
# Штатные средства: apt-cache dotty (рисунок в формате Graphviz) и
# apt-cache depends --recurse. Как и в compare_apt.sh, используется
# изолированная настройка apt с индексом СЬЮТ main. Связи Suggests в
# dotty (цвет springgreen) исключаются: инструмент их не учитывает.
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

PACKAGE="${1:?usage: compare_apt_graph.sh PACKAGE [SUITE]}"
SUITE="${2:-noble}"
MIRROR="http://archive.ubuntu.com/ubuntu"
APT_DIR="${TMP_DIR}/apt"

mkdir -p "${APT_DIR}/lists/partial" "${APT_DIR}/cache/archives/partial"
: > "${APT_DIR}/status"
echo "deb [trusted=yes] ${MIRROR} ${SUITE} main" > "${APT_DIR}/sources.list"
apt_opts=(
    -o "Dir::Etc::sourcelist=${APT_DIR}/sources.list"
    -o "Dir::Etc::sourceparts=/dev/null"
    -o "Dir::State::lists=${APT_DIR}/lists"
    -o "Dir::Cache=${APT_DIR}/cache"
    -o "Dir::State::status=${APT_DIR}/status"
    -o "Debug::NoLocking=1"
)
apt-get "${apt_opts[@]}" update -qq > /dev/null 2>&1

edges_of() {
    # Читает строки вида "a" -> "b"... и печатает пары «a b».
    sed -n -E 's/^"([^"]+)" -> "([^"]+)".*/\1 \2/p' | sort -u
}

apt-cache "${apt_opts[@]}" dotty "${PACKAGE}" > "${TMP_DIR}/dotty.txt"
grep -v springgreen "${TMP_DIR}/dotty.txt" | edges_of > "${TMP_DIR}/apt_edges.txt"
grep -c springgreen "${TMP_DIR}/dotty.txt" > "${TMP_DIR}/apt_suggests.txt" || true

python3 -m depgraph -p "${PACKAGE}" \
    -r "${MIRROR}/dists/${SUITE}/main/binary-amd64/" \
    -o "${TMP_DIR}/graph.svg" > /dev/null 2>&1 || true
edges_of < "${TMP_DIR}/graph.d2" > "${TMP_DIR}/tool_edges.txt"

recursive="$(apt-cache "${apt_opts[@]}" depends --recurse --no-recommends \
    --no-suggests --no-conflicts --no-breaks --no-replaces --no-enhances \
    "${PACKAGE}" | grep -v '^ ' | grep -vc '^<')"
tool_nodes="$(tr ' ' '\n' < "${TMP_DIR}/tool_edges.txt" | sort -u | wc -l)"

printf 'Пакет: %s, сьют: %s\n' "${PACKAGE}" "${SUITE}"
printf 'dotty:   рёбер %d (без Suggests), рёбер Suggests: %s\n' \
    "$(wc -l < "${TMP_DIR}/apt_edges.txt")" "$(cat "${TMP_DIR}/apt_suggests.txt")"
printf 'depends --recurse: настоящих пакетов %d\n' "${recursive}"
printf 'инструмент: рёбер %d, пакетов %d\n' \
    "$(wc -l < "${TMP_DIR}/tool_edges.txt")" "${tool_nodes}"
printf 'Рёбра только в dotty:       %s\n' \
    "$(comm -23 "${TMP_DIR}/apt_edges.txt" "${TMP_DIR}/tool_edges.txt" \
        | tr ' ' '>' | tr '\n' ' ')"
printf 'Рёбра только в инструменте: %s\n' \
    "$(comm -13 "${TMP_DIR}/apt_edges.txt" "${TMP_DIR}/tool_edges.txt" \
        | tr ' ' '>' | tr '\n' ' ')"

#!/usr/bin/env bash
# Сравнение порядка загрузки с настоящим apt (только Ubuntu/Debian с apt-get).
# Использование: tests/scripts/compare_apt.sh ПАКЕТ [СЬЮТ]   (по умолчанию noble)
#
# Создаётся изолированная конфигурация apt: один репозиторий
# archive.ubuntu.com/ubuntu СЬЮТ main (тот же индекс, что читает инструмент),
# пустой список установленных пакетов, Recommends не ставятся. Системные
# настройки apt не затрагиваются. apt только имитирует установку (-s).
# shellcheck source=tests/scripts/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

PACKAGE="${1:?usage: compare_apt.sh PACKAGE [SUITE]}"
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
apt-get "${apt_opts[@]}" -s install --no-install-recommends "${PACKAGE}" \
    | sed -n 's/^Inst \([^ ]*\) .*/\1/p' > "${TMP_DIR}/apt.txt"
python3 -m depgraph -p "${PACKAGE}" \
    -r "${MIRROR}/dists/${SUITE}/main/binary-amd64/" --load-order \
    | sed -n 's/^ *[0-9]*\. //p' > "${TMP_DIR}/tool.txt"

printf 'Пакет: %s, сьют: %s\n' "${PACKAGE}" "${SUITE}"
printf 'apt: %d пакетов, инструмент: %d пакетов\n' \
    "$(wc -l < "${TMP_DIR}/apt.txt")" "$(wc -l < "${TMP_DIR}/tool.txt")"
only_apt="$(comm -23 <(sort "${TMP_DIR}/apt.txt") <(sort "${TMP_DIR}/tool.txt"))"
only_tool="$(comm -13 <(sort "${TMP_DIR}/apt.txt") <(sort "${TMP_DIR}/tool.txt"))"
printf 'Только в apt:        %s\n' "${only_apt:-—}" | tr '\n' ' '; echo
printf 'Только в инструменте: %s\n' "${only_tool:-—}" | tr '\n' ' '; echo
if [ -z "${only_apt}${only_tool}" ]; then
    echo "Множества пакетов СОВПАДАЮТ"
else
    echo "Множества пакетов РАЗЛИЧАЮТСЯ"
fi
if cmp -s "${TMP_DIR}/apt.txt" "${TMP_DIR}/tool.txt"; then
    echo "Порядок загрузки СОВПАДАЕТ"
else
    echo "Порядок загрузки отличается:"
    printf '%-28s %s\n' "apt (Inst)" "инструмент"
    paste -d'|' "${TMP_DIR}/apt.txt" "${TMP_DIR}/tool.txt" \
        | awk -F'|' '{printf "%-28s %s\n", $1, $2}'
fi

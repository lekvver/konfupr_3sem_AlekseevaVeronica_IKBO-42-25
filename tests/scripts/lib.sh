#!/usr/bin/env bash
# Общие функции для сценариев тестирования эмулятора из реальной ОС.
# Подключается командой: source lib.sh (см. любой сценарий stage*.sh).

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$(dirname "${SCRIPTS_DIR}")"
ROOT_DIR="$(dirname "${TESTS_DIR}")"
STARTUP_DIR="${TESTS_DIR}/startup"
export STARTUP_DIR
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONDONTWRITEBYTECODE=1

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

FAILED=0
OUTPUT=""
STATUS=0

# Печатает заголовок очередного проверяемого случая.
show_case() {
    printf '\n=== %s ===\n' "$1"
}

# Запускает эмулятор с закрытым stdin. Весь вывод (stdout и stderr)
# сохраняется в OUTPUT, код возврата в STATUS, а на экран выводится
# в виде диалога.
run_emulator() {
    printf '$ python3 -m shell_emulator %s\n' "$*"
    OUTPUT="$(python3 -m shell_emulator "$@" 2>&1 < /dev/null)"
    STATUS=$?
    printf '%s\n' "${OUTPUT}" | sed 's/^/    /'
    printf '    [exit code: %d]\n' "${STATUS}"
}

fail() {
    printf 'FAIL: %s\n' "$*"
    FAILED=1
}

# Проверяет код возврата последнего запуска.
expect_status() {
    if [ "${STATUS}" -ne "$1" ]; then
        fail "expected exit code $1, got ${STATUS}"
    fi
}

# Проверяет, что вывод содержит заданный текст.
expect_output() {
    if ! grep -qF -- "$1" <<< "${OUTPUT}"; then
        fail "output does not contain: $1"
    fi
}

# Проверяет, что вывод не содержит заданный текст.
reject_output() {
    if grep -qF -- "$1" <<< "${OUTPUT}"; then
        fail "output must not contain: $1"
    fi
}

# Завершает сценарий: код 1, если хотя бы одна проверка не прошла.
finish() {
    if [ "${FAILED}" -eq 0 ]; then
        printf '\nPASS: %s\n' "$(basename "$0")"
    else
        printf '\nFAILED: %s\n' "$(basename "$0")"
        exit 1
    fi
}

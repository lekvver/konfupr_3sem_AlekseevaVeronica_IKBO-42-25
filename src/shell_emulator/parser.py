"""Разбор введённой строки на слова с раскрытием переменных окружения."""

from __future__ import annotations

import re
from typing import Mapping

from .errors import ParseError

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
QUOTES = SINGLE_QUOTE + DOUBLE_QUOTE
COMMENT_CHAR = "#"
NOT_FOUND = -1
VARIABLE = re.compile(
    r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))"
)


def expand_vars(text: str, env: Mapping[str, str]) -> str:
    """Подставляет значения $VAR и ${VAR}; неизвестные переменные дают ''."""

    def replace(match: re.Match[str]) -> str:
        """Возвращает значение переменной, найденной в тексте."""
        name = match.group(1) or match.group(2)
        return env.get(name, "")

    return VARIABLE.sub(replace, text)


def skip_spaces(line: str, pos: int) -> int:
    """Возвращает позицию первого непробельного символа начиная с pos."""
    while pos < len(line) and line[pos].isspace():
        pos += 1
    return pos


def read_quoted(line: str, pos: int, env: Mapping[str, str]) -> tuple[str, int]:
    """Читает фрагмент в кавычках, начинающийся в позиции pos.

    В одинарных кавычках текст сохраняется как есть, в двойных
    раскрываются переменные. Возвращает текст и позицию после кавычки.
    """
    quote = line[pos]
    end = line.find(quote, pos + 1)
    if end == NOT_FOUND:
        raise ParseError(
            f"syntax error: unexpected end of line, missing closing {quote}"
        )
    text = line[pos + 1:end]
    if quote == DOUBLE_QUOTE:
        text = expand_vars(text, env)
    return text, end + 1


def read_bare(line: str, pos: int, env: Mapping[str, str]) -> tuple[str, int]:
    """Читает фрагмент без кавычек до пробела или кавычки."""
    end = pos
    while end < len(line) and not line[end].isspace():
        if line[end] in QUOTES:
            break
        end += 1
    return expand_vars(line[pos:end], env), end


def read_word(line: str, pos: int, env: Mapping[str, str]) -> tuple[str, int]:
    """Читает одно слово, которое может состоять из нескольких фрагментов."""
    pieces = []
    while pos < len(line) and not line[pos].isspace():
        if line[pos] in QUOTES:
            text, pos = read_quoted(line, pos, env)
        else:
            text, pos = read_bare(line, pos, env)
        pieces.append(text)
    return "".join(pieces), pos


def parse_line(line: str, env: Mapping[str, str]) -> list[str]:
    """Разбивает строку на слова и раскрывает переменные окружения.

    Слова разделяются пробелами. Слово, начинающееся с #, открывает
    комментарий до конца строки. Результат подстановки переменной
    на слова не разбивается.
    """
    words = []
    pos = skip_spaces(line, 0)
    while pos < len(line) and line[pos] != COMMENT_CHAR:
        word, pos = read_word(line, pos, env)
        words.append(word)
        pos = skip_spaces(line, pos)
    return words

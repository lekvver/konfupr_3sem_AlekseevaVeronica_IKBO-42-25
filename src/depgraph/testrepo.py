"""Тестовый репозиторий: граф зависимостей, заданный текстовым файлом.

Формат: по одной строке «ИМЯ: ЗАВИСИМОСТЬ ЗАВИСИМОСТЬ ...». Имена пакетов —
заглавные латинские буквы. Пустые строки и текст после «#» игнорируются.
Пакет, который упомянут только как зависимость, считается пакетом без
зависимостей.

    A: B C
    B: C
    C:
"""

import re
from typing import Dict, List, Tuple

from depgraph.errors import RepositoryError

NAME = re.compile(r"[A-Z]+")
COMMENT_MARK = "#"


class TestRepository:
    """Граф из файла, оформленный как репозиторий."""

    __test__ = False

    def __init__(self, graph: Dict[str, List[str]]) -> None:
        """Запоминает граф и множество всех упомянутых имён."""
        self.graph = graph
        self.names = set(graph)
        for deps in graph.values():
            self.names.update(deps)

    def has_package(self, name: str) -> bool:
        """Пакет известен, если он описан или упомянут как зависимость."""
        return name in self.names

    def version(self, name: str) -> str:
        """У тестовых пакетов версий нет."""
        return ""

    def is_known(self, name: str) -> bool:
        """Все упомянутые имена известны."""
        return name in self.names

    def dependencies(self, name: str) -> List[str]:
        """Прямые зависимости в порядке записи в файле."""
        return list(self.graph.get(name, []))

    def dependency_groups(self, name: str) -> List[Tuple[str, Tuple[str, ...]]]:
        """Альтернатив в тестовом формате нет: группа из одного пакета."""
        return [(dep, (dep,)) for dep in self.dependencies(name)]


def _check_name(name: str, number: int) -> None:
    """Проверяет, что имя состоит из заглавных латинских букв."""
    if not NAME.fullmatch(name):
        raise RepositoryError(
            f"line {number}: invalid package name {name!r} "
            "(uppercase Latin letters expected)"
        )


def _parse_line(line: str, number: int) -> Tuple[str, List[str]]:
    """Разбирает строку «ИМЯ: ЗАВИСИМОСТИ»."""
    head, colon, tail = line.partition(":")
    if not colon:
        raise RepositoryError(
            f"line {number}: expected 'NAME: DEPENDENCY ...', got {line!r}"
        )
    name = head.strip()
    _check_name(name, number)
    deps: List[str] = []
    for dep in tail.replace(",", " ").split():
        _check_name(dep, number)
        if dep not in deps:
            deps.append(dep)
    return name, deps


def parse_test_repo(text: str) -> TestRepository:
    """Разбирает текст файла тестового репозитория."""
    graph: Dict[str, List[str]] = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(COMMENT_MARK, 1)[0].strip()
        if not line:
            continue
        name, deps = _parse_line(line, number)
        if name in graph:
            raise RepositoryError(
                f"line {number}: package {name} is defined twice"
            )
        graph[name] = deps
    if not graph:
        raise RepositoryError("test repository defines no packages")
    return TestRepository(graph)


def load_test_repo(path: str) -> TestRepository:
    """Читает и разбирает файл тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        raise RepositoryError(f"cannot read {path}: {error}") from error
    return parse_test_repo(text)

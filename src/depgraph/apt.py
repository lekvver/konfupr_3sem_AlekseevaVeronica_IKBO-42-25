"""Репозиторий Ubuntu (apt): загрузка и разбор индекса Packages.

Индекс — текстовый файл из абзацев «Поле: значение», абзацы разделены
пустой строкой. Прямые зависимости пакета записаны в полях Pre-Depends
и Depends, например: «libc6 (>= 2.34), debconf | debconf-2.0».
"""

import gzip
import lzma
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

from depgraph.errors import RepositoryError

TIMEOUT_SECONDS = 60
HTTP_NOT_FOUND = 404
CONTINUATION_CHARS = " \t"
INDEX_NAMES = ("Packages.gz", "Packages.xz", "Packages")
KEPT_FIELDS = (
    "Package", "Version", "Priority", "Pre-Depends", "Depends", "Provides",
)
PRIORITIES = ("required", "important", "standard", "optional", "extra")
DEPENDENCY_FIELDS = ("Pre-Depends", "Depends")
RELATION_NAME = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9+.\-]*)")

Group = Tuple[str, ...]


@dataclass(frozen=True)
class Package:
    """Запись индекса: имя, версия, группы зависимостей и Provides.

    Группа — набор альтернатив («a | b»), из которых достаточно одной.
    """

    name: str
    version: str
    groups: Tuple[Group, ...]
    provides: Tuple[str, ...]
    priority: str = ""


class IndexNotFoundError(RepositoryError):
    """Файла индекса нет по указанному адресу."""


def _relation_name(text: str) -> Optional[str]:
    """Вырезает имя пакета из «name:any (>= 1.0) [amd64]»."""
    match = RELATION_NAME.match(text)
    return match.group(1) if match else None


def parse_relations(value: str) -> List[Group]:
    """Разбирает значение поля Depends на группы альтернатив.

    Версии, архитектуры и профили сборки отбрасываются, остаются имена.
    """
    groups = []
    for part in value.split(","):
        names = [_relation_name(alt) for alt in part.split("|")]
        group = tuple(name for name in names if name)
        if group:
            groups.append(group)
    return groups


def _paragraphs(text: str) -> Iterator[Dict[str, str]]:
    """Выдаёт абзацы индекса как словари нужных полей."""
    fields: Dict[str, str] = {}
    key = ""
    for line in text.splitlines():
        if not line.strip():
            if fields:
                yield fields
            fields, key = {}, ""
        elif line[0] in CONTINUATION_CHARS:
            if key in fields:
                fields[key] += " " + line.strip()
        else:
            key, _, value = line.partition(":")
            if key in KEPT_FIELDS:
                fields[key] = value.strip()
    if fields:
        yield fields


def priority_rank(package: Package) -> int:
    """Чем меньше число, тем важнее пакет (required — самый важный)."""
    if package.priority in PRIORITIES:
        return PRIORITIES.index(package.priority)
    return len(PRIORITIES)


def _make_package(name: str, fields: Dict[str, str]) -> Package:
    """Собирает Package из полей абзаца."""
    groups: List[Group] = []
    for field in DEPENDENCY_FIELDS:
        groups.extend(parse_relations(fields.get(field, "")))
    provides = tuple(
        group[0] for group in parse_relations(fields.get("Provides", ""))
    )
    return Package(
        name,
        fields.get("Version", ""),
        tuple(groups),
        provides,
        fields.get("Priority", ""),
    )


def parse_packages(text: str) -> Dict[str, Package]:
    """Разбирает индекс Packages. При повторе имени берётся первая запись."""
    packages: Dict[str, Package] = {}
    for fields in _paragraphs(text):
        name = fields.get("Package")
        if name and name not in packages:
            packages[name] = _make_package(name, fields)
    return packages


class AptRepository:
    """Индекс пакетов с выбором альтернатив и виртуальных пакетов."""

    def __init__(self, packages: Dict[str, Package]) -> None:
        """Запоминает пакеты и строит таблицу «виртуальный -> поставщики».

        Поставщики упорядочены по приоритету пакета (required, important,
        standard, optional, extra), при равенстве — по порядку в индексе.
        """
        self.packages = packages
        self.providers: Dict[str, List[str]] = {}
        for package in packages.values():
            for virtual in package.provides:
                self.providers.setdefault(virtual, []).append(package.name)
        for names in self.providers.values():
            names.sort(key=lambda name: priority_rank(packages[name]))

    def has_package(self, name: str) -> bool:
        """Есть ли в индексе настоящий пакет с таким именем."""
        return name in self.packages

    def version(self, name: str) -> str:
        """Версия пакета или пустая строка."""
        package = self.packages.get(name)
        return package.version if package else ""

    def is_known(self, name: str) -> bool:
        """Известно ли имя: настоящий или виртуальный пакет."""
        return name in self.packages or name in self.providers

    def choose(self, group: Group) -> str:
        """Выбирает пакет из группы альтернатив.

        Берётся первая альтернатива, которая есть в индексе; затем первая
        виртуальная (её заменяет самый приоритетный поставщик). Если нет,
        возвращается первая альтернатива как есть.
        """
        for name in group:
            if name in self.packages:
                return name
        for name in group:
            if name in self.providers:
                return self.providers[name][0]
        return group[0]

    def dependency_groups(self, name: str) -> List[Tuple[str, Group]]:
        """Для каждой зависимости: (выбранный пакет, группа альтернатив).

        Повторы по выбранному пакету отбрасываются, порядок — как в индексе.
        """
        package = self.packages.get(name)
        if package is None:
            return []
        result: List[Tuple[str, Group]] = []
        seen = set()
        for group in package.groups:
            chosen = self.choose(group)
            if chosen not in seen:
                seen.add(chosen)
                result.append((chosen, group))
        return result

    def dependencies(self, name: str) -> List[str]:
        """Прямые зависимости пакета без повторов, в порядке индекса."""
        return [chosen for chosen, _ in self.dependency_groups(name)]


def index_urls(url: str) -> List[str]:
    """Возвращает адреса, по которым ищется индекс.

    Если URL уже указывает на файл Packages[.gz|.xz], берётся он сам,
    иначе URL считается каталогом, где лежит индекс.
    """
    last = url.rstrip("/").rsplit("/", 1)[-1]
    if last in INDEX_NAMES:
        return [url]
    base = url if url.endswith("/") else url + "/"
    return [base + name for name in INDEX_NAMES]


def download(url: str) -> bytes:
    """Скачивает файл по URL (http, https или file)."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as reply:
            return reply.read()
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise IndexNotFoundError(url) from error
        raise RepositoryError(f"cannot download {url}: {error}") from error
    except urllib.error.URLError as error:
        if isinstance(error.reason, FileNotFoundError):
            raise IndexNotFoundError(url) from error
        raise RepositoryError(f"cannot download {url}: {error.reason}") \
            from error
    except (OSError, ValueError) as error:
        raise RepositoryError(f"cannot download {url}: {error}") from error


def decompress(url: str, data: bytes) -> str:
    """Распаковывает индекс по расширению и декодирует в текст."""
    try:
        if url.endswith(".gz"):
            data = gzip.decompress(data)
        elif url.endswith(".xz"):
            data = lzma.decompress(data)
    except (OSError, EOFError, lzma.LZMAError) as error:
        raise RepositoryError(f"broken index {url}: {error}") from error
    return data.decode("utf-8", errors="replace")


def load_repository(url: str) -> AptRepository:
    """Загружает индекс пакетов по URL репозитория."""
    missing = []
    for candidate in index_urls(url):
        try:
            data = download(candidate)
        except IndexNotFoundError:
            missing.append(candidate)
            continue
        packages = parse_packages(decompress(candidate, data))
        if not packages:
            raise RepositoryError(f"no packages found in {candidate}")
        return AptRepository(packages)
    raise RepositoryError("package index not found, tried: " + ", ".join(
        missing))

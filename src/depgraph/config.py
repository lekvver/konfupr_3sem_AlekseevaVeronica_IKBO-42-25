"""Параметры командной строки и их проверка."""

import argparse
import os
import re
from dataclasses import dataclass
from typing import List, NoReturn, Optional, Sequence, Tuple
from urllib.parse import urlparse

from depgraph.errors import ConfigError

DEFAULT_OUTPUT = "graph.svg"
SVG_SUFFIX = ".svg"
URL_SCHEMES = ("http", "https", "file")
APT_NAME = re.compile(r"[a-z0-9][a-z0-9+.\-]+")
TEST_NAME = re.compile(r"[A-Z]+")


@dataclass(frozen=True)
class Config:
    """Все параметры, которые задаёт пользователь."""

    package: str
    repo: str
    test_mode: bool
    output: str
    print_params: bool = False
    direct: bool = False
    load_order: bool = False

    def as_pairs(self) -> List[Tuple[str, str]]:
        """Возвращает параметры как пары (ключ, значение) для вывода."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("test_mode", "true" if self.test_mode else "false"),
            ("output", self.output),
        ]


class _Parser(argparse.ArgumentParser):
    """Разборщик, который сообщает об ошибках исключением."""

    def error(self, message: str) -> NoReturn:
        """Вместо печати справки и выхода возбуждает ConfigError."""
        raise ConfigError(message)


def build_parser() -> argparse.ArgumentParser:
    """Создаёт разборщик параметров командной строки."""
    parser = _Parser(
        prog="depgraph",
        description="Граф зависимостей пакета Ubuntu (apt).",
    )
    parser.add_argument(
        "-p", "--package", required=True, metavar="NAME",
        help="имя анализируемого пакета",
    )
    parser.add_argument(
        "-r", "--repo", required=True, metavar="URL|PATH",
        help="URL репозитория или путь к файлу тестового репозитория",
    )
    parser.add_argument(
        "-t", "--test-mode", action="store_true",
        help="режим тестового репозитория: --repo задаёт путь к файлу",
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT, metavar="FILE",
        help="имя файла с изображением графа, .svg (по умолчанию "
        f"{DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--print-params", action="store_true",
        help="вывести все параметры в формате ключ = значение",
    )
    parser.add_argument(
        "--direct", action="store_true",
        help="вывести только прямые зависимости пакета (этап 2)",
    )
    parser.add_argument(
        "--load-order", action="store_true",
        help="вывести порядок загрузки зависимостей пакета (этап 4)",
    )
    return parser


def check_package(name: str, test_mode: bool) -> None:
    """Проверяет имя пакета: apt-имя или заглавные латинские буквы."""
    if not name.strip():
        raise ConfigError("package name must not be empty")
    if test_mode:
        pattern, rule = TEST_NAME, "uppercase Latin letters (A-Z)"
    else:
        pattern = APT_NAME
        rule = "lowercase letters, digits and + - . (min 2 chars)"
    if not pattern.fullmatch(name):
        raise ConfigError(f"invalid package name {name!r}: use {rule}")


def check_repo_url(url: str) -> None:
    """Проверяет, что адрес репозитория является URL."""
    parts = urlparse(url)
    if parts.scheme not in URL_SCHEMES:
        raise ConfigError(
            f"invalid repository URL {url!r}: expected http://, https:// "
            "or file:// (use --test-mode to read a test repository file)"
        )
    if not parts.netloc and parts.scheme != "file":
        raise ConfigError(f"invalid repository URL {url!r}: no host")


def check_repo_file(path: str) -> None:
    """Проверяет, что путь указывает на читаемый файл."""
    if not os.path.exists(path):
        raise ConfigError(f"test repository file not found: {path}")
    if os.path.isdir(path):
        raise ConfigError(f"test repository is a directory: {path}")
    if not os.path.isfile(path):
        raise ConfigError(f"test repository is not a regular file: {path}")
    if not os.access(path, os.R_OK):
        raise ConfigError(f"test repository file is not readable: {path}")


def check_repo(repo: str, test_mode: bool) -> None:
    """Проверяет параметр --repo в зависимости от режима."""
    if not repo.strip():
        raise ConfigError("repository must not be empty")
    if test_mode:
        check_repo_file(repo)
    else:
        check_repo_url(repo)


def check_output(path: str) -> None:
    """Проверяет имя файла изображения: расширение и каталог."""
    if not path.strip():
        raise ConfigError("output file name must not be empty")
    if os.path.splitext(path)[1].lower() != SVG_SUFFIX:
        raise ConfigError(f"output file must have .svg extension: {path}")
    if os.path.isdir(path):
        raise ConfigError(f"output path is a directory: {path}")
    folder = os.path.dirname(path) or "."
    if not os.path.isdir(folder):
        raise ConfigError(f"output directory does not exist: {folder}")
    if not os.access(folder, os.W_OK):
        raise ConfigError(f"output directory is not writable: {folder}")


def check_actions(config: Config) -> None:
    """Режимы --direct и --load-order нельзя включить одновременно."""
    if config.direct and config.load_order:
        raise ConfigError("--direct and --load-order are mutually exclusive")


def validate(config: Config) -> None:
    """Проверяет все параметры; при ошибке возбуждает ConfigError."""
    check_actions(config)
    check_package(config.package, config.test_mode)
    check_repo(config.repo, config.test_mode)
    check_output(config.output)


def parse_config(argv: Optional[Sequence[str]] = None) -> Config:
    """Разбирает параметры командной строки и проверяет их."""
    args = build_parser().parse_args(argv)
    config = Config(
        package=args.package,
        repo=args.repo,
        test_mode=args.test_mode,
        output=args.output,
        print_params=args.print_params,
        direct=args.direct,
        load_order=args.load_order,
    )
    validate(config)
    return config

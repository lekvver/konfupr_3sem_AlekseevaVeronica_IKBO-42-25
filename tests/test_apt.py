"""Тесты разбора индекса Packages и выбора зависимостей."""

import gzip
import lzma
import os
import tempfile
import unittest

from depgraph.apt import (
    AptRepository,
    index_urls,
    load_repository,
    parse_packages,
    parse_relations,
)
from depgraph.errors import RepositoryError

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "index")
INDEX_FILE = os.path.join(DATA_DIR, "Packages")


def read_index() -> str:
    """Читает тестовый индекс."""
    with open(INDEX_FILE, encoding="utf-8") as handle:
        return handle.read()


class ParseRelationsTest(unittest.TestCase):
    """Разбор значения поля Depends."""

    def test_versions_are_dropped(self):
        """Ограничения версий отбрасываются."""
        self.assertEqual(
            parse_relations("libc6 (>= 2.34), zlib1g"),
            [("libc6",), ("zlib1g",)],
        )

    def test_alternatives(self):
        """Альтернативы собираются в одну группу."""
        self.assertEqual(
            parse_relations("debconf (>= 0.5) | debconf-2.0"),
            [("debconf", "debconf-2.0")],
        )

    def test_arch_qualifier_and_restriction(self):
        """Архитектурные уточнения не попадают в имя."""
        self.assertEqual(
            parse_relations("python3:any, libx [amd64] <!nocheck>"),
            [("python3",), ("libx",)],
        )

    def test_empty_value(self):
        """Пустое значение даёт пустой список."""
        self.assertEqual(parse_relations(""), [])


class ParsePackagesTest(unittest.TestCase):
    """Разбор всего индекса."""

    def setUp(self):
        """Разбирает тестовый индекс."""
        self.packages = parse_packages(read_index())

    def test_all_packages_found(self):
        """Повтор имени не создаёт второй записи."""
        self.assertEqual(len(self.packages), 11)

    def test_first_duplicate_wins(self):
        """При повторе имени остаётся первая запись."""
        self.assertEqual(self.packages["dup"].version, "first")

    def test_continuation_line(self):
        """Строки продолжения склеиваются с полем."""
        groups = self.packages["app"].groups
        self.assertIn(("mail-agent",), groups)
        self.assertIn(("missing-pkg",), groups)

    def test_pre_depends_come_first(self):
        """Сначала идут Pre-Depends, затем Depends."""
        self.assertEqual(self.packages["app"].groups[0], ("base",))

    def test_other_fields_ignored(self):
        """Recommends не считается зависимостью."""
        names = [n for g in self.packages["app"].groups for n in g]
        self.assertNotIn("ignored-recommend", names)

    def test_no_trailing_blank_line(self):
        """Последний абзац без пустой строки в конце читается."""
        packages = parse_packages("Package: x\nVersion: 1\nDepends: y")
        self.assertEqual(packages["x"].groups, (("y",),))


class AptRepositoryTest(unittest.TestCase):
    """Выбор альтернатив и виртуальных пакетов."""

    def setUp(self):
        """Создаёт репозиторий из тестового индекса."""
        self.repo = AptRepository(parse_packages(read_index()))

    def test_direct_dependencies(self):
        """Прямые зависимости: без повторов, в порядке индекса."""
        self.assertEqual(
            self.repo.dependencies("app"),
            ["base", "libfoo", "libbaz", "mta-one", "missing-pkg"],
        )

    def test_virtual_package_uses_first_provider(self):
        """Виртуальный пакет заменяется первым поставщиком."""
        self.assertEqual(self.repo.choose(("mail-agent",)), "mta-one")

    def test_provider_with_higher_priority_wins(self):
        """Из поставщиков выбирается пакет с более высоким приоритетом."""
        self.assertEqual(self.repo.choose(("awk",)), "awk-mawk")

    def test_real_alternative_preferred(self):
        """Настоящий пакет предпочтительнее виртуального."""
        self.assertEqual(self.repo.choose(("mail-agent", "base")), "base")

    def test_unknown_group_keeps_first_name(self):
        """Неизвестная группа остаётся как есть."""
        self.assertEqual(self.repo.choose(("nothing", "none")), "nothing")

    def test_is_known(self):
        """Известны настоящие и виртуальные имена."""
        self.assertTrue(self.repo.is_known("mail-agent"))
        self.assertFalse(self.repo.is_known("missing-pkg"))

    def test_has_package_only_real(self):
        """has_package не считает виртуальные имена пакетами."""
        self.assertTrue(self.repo.has_package("app"))
        self.assertFalse(self.repo.has_package("mail-agent"))

    def test_unknown_package_has_no_dependencies(self):
        """У неизвестного пакета зависимостей нет."""
        self.assertEqual(self.repo.dependencies("zzz"), [])


class LoadRepositoryTest(unittest.TestCase):
    """Загрузка индекса по URL."""

    def test_directory_url(self):
        """URL каталога: берётся Packages из этого каталога."""
        repo = load_repository("file://" + DATA_DIR)
        self.assertTrue(repo.has_package("app"))

    def test_compressed_indexes(self):
        """Поддерживаются Packages.gz и Packages.xz."""
        raw = read_index().encode("utf-8")
        packers = {"Packages.gz": gzip.compress, "Packages.xz": lzma.compress}
        for name, pack in packers.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as folder:
                    with open(os.path.join(folder, name), "wb") as handle:
                        handle.write(pack(raw))
                    repo = load_repository("file://" + folder + "/")
                    self.assertTrue(repo.has_package("libfoo"))

    def test_file_url(self):
        """URL может указывать прямо на файл индекса."""
        repo = load_repository("file://" + INDEX_FILE)
        self.assertTrue(repo.has_package("base"))

    def test_index_missing(self):
        """Нет индекса: ошибка со списком проверенных адресов."""
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RepositoryError, "Packages.gz"):
                load_repository("file://" + folder)

    def test_broken_archive(self):
        """Повреждённый архив даёт RepositoryError."""
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "Packages.gz"), "wb") as handle:
                handle.write(b"not a gzip")
            with self.assertRaisesRegex(RepositoryError, "broken index"):
                load_repository("file://" + folder)

    def test_empty_index(self):
        """Индекс без пакетов недопустим."""
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "Packages"), "w") as handle:
                handle.write("\n\n")
            with self.assertRaisesRegex(RepositoryError, "no packages"):
                load_repository("file://" + folder)

    def test_index_urls(self):
        """Варианты адреса индекса."""
        self.assertEqual(
            index_urls("http://h/d"),
            ["http://h/d/Packages.gz", "http://h/d/Packages.xz",
             "http://h/d/Packages"],
        )
        self.assertEqual(index_urls("http://h/Packages.xz"),
                         ["http://h/Packages.xz"])

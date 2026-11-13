"""Тесты разбора файла тестового репозитория."""

import os
import unittest

from depgraph.errors import RepositoryError
from depgraph.testrepo import load_test_repo, parse_test_repo
from helpers import DATA_DIR, temp_file

REPOS_DIR = os.path.join(os.path.dirname(DATA_DIR), "repos")


class ParseTestRepoTest(unittest.TestCase):
    """Разбор текста."""

    def test_simple(self):
        """Строки «ИМЯ: ЗАВИСИМОСТИ» превращаются в граф."""
        repo = parse_test_repo("A: B C\nB: C\nC:\n")
        self.assertEqual(repo.dependencies("A"), ["B", "C"])
        self.assertEqual(repo.dependencies("C"), [])

    def test_comments_commas_duplicates(self):
        """Комментарии, запятые и повторы допустимы."""
        repo = parse_test_repo("# заголовок\nA: B, C, B  # конец\n\n")
        self.assertEqual(repo.dependencies("A"), ["B", "C"])

    def test_undefined_dependency_is_leaf(self):
        """Пакет, упомянутый только как зависимость, существует."""
        repo = parse_test_repo("A: Z\n")
        self.assertTrue(repo.has_package("Z"))
        self.assertEqual(repo.dependencies("Z"), [])
        self.assertFalse(repo.has_package("Q"))

    def test_groups_have_one_alternative(self):
        """Группы альтернатив состоят из одного пакета."""
        repo = parse_test_repo("A: B\n")
        self.assertEqual(repo.dependency_groups("A"), [("B", ("B",))])

    def test_missing_colon(self):
        """Строка без двоеточия — ошибка с номером строки."""
        with self.assertRaisesRegex(RepositoryError, "line 2: expected"):
            parse_test_repo("A: B\nB C\n")

    def test_lowercase_name(self):
        """Имя из строчных букв недопустимо."""
        with self.assertRaisesRegex(RepositoryError, "line 1: invalid"):
            parse_test_repo("a: B\n")

    def test_bad_dependency_name(self):
        """Недопустимое имя зависимости."""
        with self.assertRaisesRegex(RepositoryError, "invalid package name"):
            parse_test_repo("A: B1\n")

    def test_duplicate_definition(self):
        """Повторное описание пакета — ошибка."""
        with self.assertRaisesRegex(RepositoryError, "defined twice"):
            parse_test_repo("A: B\nA: C\n")

    def test_empty_file(self):
        """Файл без пакетов недопустим."""
        for text in ("", "\n# только комментарий\n"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(RepositoryError, "no packages"):
                    parse_test_repo(text)


class LoadTestRepoTest(unittest.TestCase):
    """Чтение файла."""

    def test_load_file(self):
        """Файл из каталога tests/repos читается."""
        repo = load_test_repo(os.path.join(REPOS_DIR, "diamond.txt"))
        self.assertEqual(repo.dependencies("B"), ["D"])

    def test_not_utf8(self):
        """Файл не в UTF-8 даёт RepositoryError."""
        with temp_file("") as path:
            with open(path, "wb") as handle:
                handle.write(b"\xff\xfe\x00")
            with self.assertRaisesRegex(RepositoryError, "cannot read"):
                load_test_repo(path)

    def test_all_sample_repos_are_valid(self):
        """Все файлы tests/repos разбираются без ошибок."""
        for name in sorted(os.listdir(REPOS_DIR)):
            with self.subTest(name=name):
                load_test_repo(os.path.join(REPOS_DIR, name))

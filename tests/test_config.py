"""Тесты разбора и проверки параметров командной строки."""

import os
import tempfile
import unittest

from depgraph.config import DEFAULT_OUTPUT, parse_config
from depgraph.errors import ConfigError
from helpers import temp_file

URL = "http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/"


class ValidParamsTest(unittest.TestCase):
    """Корректные наборы параметров."""

    def test_real_mode_defaults(self):
        """Режим по умолчанию — реальный репозиторий, вывод graph.svg."""
        config = parse_config(["-p", "bash", "-r", URL])
        self.assertEqual(config.package, "bash")
        self.assertEqual(config.repo, URL)
        self.assertFalse(config.test_mode)
        self.assertEqual(config.output, DEFAULT_OUTPUT)

    def test_long_option_names(self):
        """Длинные имена параметров работают так же, как короткие."""
        with temp_file("A:\n") as path:
            config = parse_config([
                "--package", "A", "--repo", path, "--test-mode",
                "--output", "out.svg",
            ])
        self.assertTrue(config.test_mode)
        self.assertEqual(config.output, "out.svg")

    def test_file_url_is_accepted(self):
        """URL со схемой file:// допустим (для проверок без сети)."""
        config = parse_config(["-p", "bash", "-r", "file:///tmp/repo/"])
        self.assertEqual(config.repo, "file:///tmp/repo/")

    def test_as_pairs_order(self):
        """Пары ключ-значение идут в фиксированном порядке."""
        config = parse_config(["-p", "g++", "-r", URL])
        keys = [key for key, _ in config.as_pairs()]
        self.assertEqual(keys, ["package", "repo", "test_mode", "output"])


class PackageErrorsTest(unittest.TestCase):
    """Ошибки в имени пакета."""

    def test_missing_package(self):
        """Параметр --package обязателен."""
        with self.assertRaises(ConfigError):
            parse_config(["-r", URL])

    def test_empty_package(self):
        """Пустое имя пакета недопустимо."""
        with self.assertRaisesRegex(ConfigError, "must not be empty"):
            parse_config(["-p", " ", "-r", URL])

    def test_uppercase_in_real_mode(self):
        """В реальном режиме имя пакета записывается строчными буквами."""
        with self.assertRaisesRegex(ConfigError, "invalid package name"):
            parse_config(["-p", "Bash", "-r", URL])

    def test_bad_symbols(self):
        """Пробелы и спецсимволы в имени недопустимы."""
        for name in ("ba sh", "bash!", "a", "-bash"):
            with self.subTest(name=name):
                with self.assertRaises(ConfigError):
                    parse_config(["-p", name, "-r", URL])

    def test_lowercase_in_test_mode(self):
        """В тестовом режиме имена — только заглавные латинские буквы."""
        with temp_file("A:\n") as path:
            for name in ("a", "A1", "AB-C"):
                with self.subTest(name=name):
                    with self.assertRaises(ConfigError):
                        parse_config(["-p", name, "-r", path, "-t"])


class RepoErrorsTest(unittest.TestCase):
    """Ошибки в адресе репозитория."""

    def test_missing_repo(self):
        """Параметр --repo обязателен."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "bash"])

    def test_empty_repo(self):
        """Пустой адрес недопустим."""
        with self.assertRaisesRegex(ConfigError, "must not be empty"):
            parse_config(["-p", "bash", "-r", ""])

    def test_path_instead_of_url(self):
        """Путь к файлу без --test-mode не принимается как URL."""
        with self.assertRaisesRegex(ConfigError, "invalid repository URL"):
            parse_config(["-p", "bash", "-r", "/tmp/repo.txt"])

    def test_unsupported_scheme(self):
        """Схема ftp:// не поддерживается."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "bash", "-r", "ftp://host/ubuntu"])

    def test_url_without_host(self):
        """У http-адреса должен быть хост."""
        with self.assertRaisesRegex(ConfigError, "no host"):
            parse_config(["-p", "bash", "-r", "http://"])

    def test_test_repo_not_found(self):
        """Несуществующий файл тестового репозитория."""
        with self.assertRaisesRegex(ConfigError, "not found"):
            parse_config(["-p", "A", "-r", "/no/such/file", "-t"])

    def test_test_repo_is_directory(self):
        """Каталог вместо файла тестового репозитория."""
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ConfigError, "directory"):
                parse_config(["-p", "A", "-r", folder, "-t"])

    def test_url_in_test_mode(self):
        """В тестовом режиме URL не является путём к файлу."""
        with self.assertRaisesRegex(ConfigError, "not found"):
            parse_config(["-p", "A", "-r", URL, "-t"])


class OutputErrorsTest(unittest.TestCase):
    """Ошибки в имени файла с изображением."""

    def test_wrong_extension(self):
        """Расширение должно быть .svg."""
        with self.assertRaisesRegex(ConfigError, r"\.svg"):
            parse_config(["-p", "bash", "-r", URL, "-o", "graph.png"])

    def test_empty_output(self):
        """Пустое имя файла недопустимо."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "bash", "-r", URL, "-o", ""])

    def test_missing_directory(self):
        """Каталог для файла должен существовать."""
        with self.assertRaisesRegex(ConfigError, "does not exist"):
            parse_config(["-p", "bash", "-r", URL, "-o", "/no/dir/g.svg"])

    def test_output_is_directory(self):
        """Имя файла не может совпадать с именем каталога."""
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "x.svg")
            os.mkdir(target)
            with self.assertRaisesRegex(ConfigError, "directory"):
                parse_config(["-p", "bash", "-r", URL, "-o", target])


class UnknownOptionTest(unittest.TestCase):
    """Неизвестные параметры."""

    def test_unknown_option(self):
        """Неизвестный параметр приводит к ConfigError."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "bash", "-r", URL, "--bogus"])

    def test_option_without_value(self):
        """Параметр без значения приводит к ConfigError."""
        with self.assertRaises(ConfigError):
            parse_config(["-p", "bash", "-r"])

"""Тесты виртуальной файловой системы и команды vfs-save."""

import os
import tempfile
import unittest

from helpers import make_shell
from shell_emulator.errors import VfsError
from shell_emulator.vfs import Vfs, VfsDir, VfsFile

TREE = {
    "a.txt": b"A\n",
    "docs/b.txt": b"B\n",
    "docs/deep/c.bin": b"\x00\xff\x10binary",
}


def snapshot(root):
    """Возвращает {относительный путь: содержимое, None для каталога}."""
    result = {}
    for folder, dirnames, filenames in os.walk(root):
        for name in dirnames:
            path = os.path.join(folder, name)
            result[os.path.relpath(path, root)] = None
        for name in filenames:
            path = os.path.join(folder, name)
            with open(path, "rb") as stream:
                result[os.path.relpath(path, root)] = stream.read()
    return result


class VfsTestCase(unittest.TestCase):
    """Базовый класс: временный каталог и построение деревьев на диске."""

    def setUp(self):
        """Создаёт временный каталог перед каждым тестом."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, *parts):
        """Возвращает путь внутри временного каталога."""
        return os.path.join(self.tmp.name, *parts)

    def make_tree(self, files=None, name="src"):
        """Создаёт на диске каталог name с файлами из словаря files."""
        root = self.path(name)
        os.makedirs(root)
        for rel, data in (files or {}).items():
            target = os.path.join(root, *rel.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as stream:
                stream.write(data)
        return root


class LoadTest(VfsTestCase):
    """Загрузка VFS из каталога на диске."""

    def test_nested_tree(self):
        """Дерево каталогов и файлов целиком загружается в память."""
        vfs = Vfs.from_directory(self.make_tree(TREE))
        docs = vfs.root.children["docs"]
        self.assertIsInstance(docs, VfsDir)
        self.assertEqual(sorted(vfs.root.children), ["a.txt", "docs"])
        leaf = docs.children["deep"].children["c.bin"]
        self.assertIsInstance(leaf, VfsFile)
        self.assertEqual(leaf.data, b"\x00\xff\x10binary")

    def test_count(self):
        """count возвращает число каталогов (без корня) и файлов."""
        vfs = Vfs.from_directory(self.make_tree(TREE))
        self.assertEqual(vfs.count(), (2, 3))

    def test_empty_directory(self):
        """Пустой каталог — корректная пустая VFS."""
        vfs = Vfs.from_directory(self.make_tree())
        self.assertEqual(vfs.count(), (0, 0))

    def test_root_name(self):
        """Имя корня совпадает с именем каталога-источника."""
        vfs = Vfs.from_directory(self.make_tree(name="my_vfs"))
        self.assertEqual(vfs.root.name, "my_vfs")

    def test_source_is_not_modified(self):
        """Загрузка не меняет данные на диске."""
        root = self.make_tree(TREE)
        before = snapshot(root)
        Vfs.from_directory(root)
        self.assertEqual(snapshot(root), before)

    def test_data_is_kept_in_memory(self):
        """После загрузки изменения на диске VFS не затрагивают."""
        root = self.make_tree({"f.txt": b"old"})
        vfs = Vfs.from_directory(root)
        with open(os.path.join(root, "f.txt"), "wb") as stream:
            stream.write(b"new")
        vfs.save(self.path("out"))
        self.assertEqual(snapshot(self.path("out")), {"f.txt": b"old"})

    def test_missing_path(self):
        """Несуществующий путь — ошибка загрузки."""
        with self.assertRaises(VfsError) as ctx:
            Vfs.from_directory(self.path("nope"))
        self.assertIn("VFS not found", str(ctx.exception))

    def test_file_instead_of_directory(self):
        """Файл вместо каталога — неверный формат."""
        path = self.path("file.txt")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("x")
        with self.assertRaises(VfsError) as ctx:
            Vfs.from_directory(path)
        self.assertIn("invalid VFS format", str(ctx.exception))

    def test_symbolic_link_is_invalid(self):
        """Символическая ссылка внутри VFS — неверный формат."""
        root = self.make_tree({"f.txt": b"x"})
        try:
            os.symlink("f.txt", os.path.join(root, "link"))
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are not available")
        with self.assertRaises(VfsError) as ctx:
            Vfs.from_directory(root)
        self.assertIn("invalid VFS format", str(ctx.exception))


class DefaultVfsTest(unittest.TestCase):
    """VFS по умолчанию создаётся в памяти."""

    def test_structure(self):
        """В VFS по умолчанию есть etc/motd, home/user и tmp."""
        root = Vfs.default().root
        self.assertEqual(sorted(root.children), ["etc", "home", "tmp"])
        self.assertIn("motd", root.children["etc"].children)
        self.assertIn("user", root.children["home"].children)

    def test_count(self):
        """В VFS по умолчанию 4 каталога и 1 файл."""
        self.assertEqual(Vfs.default().count(), (4, 1))


class SaveTest(VfsTestCase):
    """Сохранение VFS на диск."""

    def test_round_trip(self):
        """Сохранённое дерево совпадает с исходным, включая байты."""
        root = self.make_tree(TREE)
        Vfs.from_directory(root).save(self.path("out"))
        self.assertEqual(snapshot(self.path("out")), snapshot(root))

    def test_empty_directories_are_saved(self):
        """Пустые каталоги тоже сохраняются."""
        Vfs.default().save(self.path("out"))
        saved = snapshot(self.path("out"))
        self.assertEqual(saved["home/user"], None)
        self.assertEqual(saved["tmp"], None)
        self.assertIn(b"Welcome", saved["etc/motd"])

    def test_creates_parent_directories(self):
        """Недостающие каталоги пути создаются."""
        Vfs.default().save(self.path("a", "b", "out"))
        self.assertTrue(os.path.isdir(self.path("a", "b", "out", "etc")))

    def test_existing_empty_directory_is_allowed(self):
        """Пустой существующий каталог подходит для сохранения."""
        os.mkdir(self.path("out"))
        Vfs.default().save(self.path("out"))
        self.assertIn("etc/motd", snapshot(self.path("out")))

    def test_source_is_not_modified(self):
        """Сохранение не меняет исходный каталог."""
        root = self.make_tree(TREE)
        before = snapshot(root)
        Vfs.from_directory(root).save(self.path("out"))
        self.assertEqual(snapshot(root), before)

    def test_target_is_a_file(self):
        """Путь к существующему файлу — ошибка."""
        path = self.path("file.txt")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("x")
        with self.assertRaises(VfsError) as ctx:
            Vfs.default().save(path)
        self.assertIn("not a directory", str(ctx.exception))

    def test_target_is_not_empty(self):
        """Непустой каталог не перезаписывается."""
        root = self.make_tree({"keep.txt": b"keep"}, name="out")
        with self.assertRaises(VfsError) as ctx:
            Vfs.default().save(root)
        self.assertIn("not empty", str(ctx.exception))
        self.assertEqual(snapshot(root), {"keep.txt": b"keep"})

    def test_target_inside_source(self):
        """Сохранять внутрь каталога-источника нельзя."""
        root = self.make_tree()
        vfs = Vfs.from_directory(root)
        for target in (root, os.path.join(root, "sub")):
            with self.assertRaises(VfsError) as ctx:
                vfs.save(target)
            self.assertIn("source directory", str(ctx.exception))
        self.assertEqual(snapshot(root), {})

    def test_cannot_create_directory(self):
        """Ошибка записи на диск превращается в VfsError."""
        path = self.path("file.txt")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("x")
        with self.assertRaises(VfsError):
            Vfs.default().save(os.path.join(path, "sub"))


class VfsSaveCommandTest(VfsTestCase):
    """Команда vfs-save в оболочке."""

    def run_lines(self, *lines):
        """Выполняет строки в оболочке с VFS по умолчанию."""
        shell = make_shell(lines)
        shell.run()
        return shell

    def test_saves_vfs(self):
        """vfs-save ПУТЬ записывает VFS на диск и сообщает об этом."""
        out = self.path("out")
        shell = self.run_lines(f'vfs-save "{out}"', "exit")
        self.assertEqual(shell.out.getvalue(), f"VFS saved to {out}\n")
        self.assertTrue(os.path.isfile(os.path.join(out, "etc", "motd")))

    def test_path_with_variable(self):
        """Путь может содержать переменную окружения."""
        out = self.path("from_env")
        shell = make_shell(["vfs-save $OUT", "exit"], env={"OUT": out})
        shell.run()
        self.assertTrue(os.path.isdir(out))

    def test_missing_operand(self):
        """Без аргумента — сообщение об ошибке."""
        shell = self.run_lines("vfs-save", "exit")
        self.assertEqual(
            shell.err.getvalue(), "vfs-save: missing path operand\n"
        )

    def test_too_many_arguments(self):
        """Лишние аргументы — сообщение об ошибке, на диск ничего не пишется."""
        shell = self.run_lines(f"vfs-save {self.path('a')} b", "exit")
        self.assertEqual(shell.err.getvalue(), "vfs-save: too many arguments\n")
        self.assertFalse(os.path.exists(self.path("a")))

    def test_error_is_reported_and_work_continues(self):
        """Ошибка сохранения выводится, следующая команда выполняется."""
        out = self.path("out")
        shell = self.run_lines(f"vfs-save {out}", f"vfs-save {out}", "ls")
        self.assertIn("vfs-save: cannot save VFS", shell.err.getvalue())
        self.assertIn("is not empty", shell.err.getvalue())
        self.assertIn("ls: args=[]", shell.out.getvalue())


if __name__ == "__main__":
    unittest.main()

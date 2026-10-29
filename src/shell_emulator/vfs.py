"""Виртуальная файловая система (VFS), целиком хранящаяся в памяти."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Union

from .errors import VfsError

DEFAULT_ROOT_NAME = "default"
DEFAULT_MOTD = b"Welcome to the virtual file system\n"


@dataclass
class VfsFile:
    """Файл VFS: имя и содержимое в виде байтов."""

    name: str
    data: bytes = b""


@dataclass
class VfsDir:
    """Каталог VFS: имя и вложенные элементы, ключ — имя элемента."""

    name: str
    children: dict[str, VfsNode] = field(default_factory=dict)


VfsNode = Union[VfsFile, VfsDir]


def disk_error(action: str, path: str, exc: OSError) -> VfsError:
    """Создаёт VfsError для сбоя операции с диском."""
    return VfsError(f"cannot {action} {path}: {exc.strerror or exc}")


def read_file(path: str) -> bytes:
    """Читает файл с диска целиком."""
    try:
        with open(path, "rb") as stream:
            return stream.read()
    except OSError as exc:
        raise disk_error("read", path, exc) from exc


def read_entry(entry: os.DirEntry[str]) -> VfsNode:
    """Читает один элемент каталога: файл или вложенный каталог.

    Ссылки и специальные файлы не поддерживаются, это неверный формат.
    """
    if entry.is_symlink():
        raise VfsError(
            f"invalid VFS format: symbolic link is not supported: {entry.path}"
        )
    if entry.is_dir(follow_symlinks=False):
        return read_directory(entry.path, entry.name)
    if entry.is_file(follow_symlinks=False):
        return VfsFile(entry.name, read_file(entry.path))
    raise VfsError(f"invalid VFS format: unsupported file type: {entry.path}")


def read_directory(path: str, name: str) -> VfsDir:
    """Рекурсивно читает каталог с диска в память."""
    try:
        with os.scandir(path) as entries:
            found = sorted(entries, key=lambda entry: entry.name)
    except OSError as exc:
        raise disk_error("read", path, exc) from exc
    directory = VfsDir(name)
    for entry in found:
        directory.children[entry.name] = read_entry(entry)
    return directory


def write_directory(directory: VfsDir, path: str) -> None:
    """Записывает содержимое каталога VFS в существующий каталог path."""
    for name, node in directory.children.items():
        target = os.path.join(path, name)
        if isinstance(node, VfsDir):
            os.mkdir(target)
            write_directory(node, target)
        else:
            with open(target, "wb") as stream:
                stream.write(node.data)


def count_nodes(directory: VfsDir) -> tuple[int, int]:
    """Считает вложенные каталоги и файлы (сам каталог не учитывается)."""
    dirs = files = 0
    for node in directory.children.values():
        if isinstance(node, VfsDir):
            sub_dirs, sub_files = count_nodes(node)
            dirs += 1 + sub_dirs
            files += sub_files
        else:
            files += 1
    return dirs, files


def add_dir(parent: VfsDir, name: str) -> VfsDir:
    """Создаёт пустой каталог name внутри parent и возвращает его."""
    child = VfsDir(name)
    parent.children[name] = child
    return child


def make_default_root() -> VfsDir:
    """Строит дерево VFS по умолчанию: /etc/motd, /home/user, /tmp."""
    root = VfsDir(DEFAULT_ROOT_NAME)
    etc = add_dir(root, "etc")
    etc.children["motd"] = VfsFile("motd", DEFAULT_MOTD)
    home = add_dir(root, "home")
    add_dir(home, "user")
    add_dir(root, "tmp")
    return root


def is_inside(path: str, parent: str) -> bool:
    """Проверяет, что path совпадает с parent или лежит внутри него."""
    path, parent = os.path.realpath(path), os.path.realpath(parent)
    try:
        return os.path.commonpath([path, parent]) == parent
    except ValueError:
        return False


def check_save_target(path: str, source: str | None) -> None:
    """Проверяет, что VFS можно сохранить в path, не затронув чужие данные.

    Путь не должен лежать внутри каталога-источника, а если он уже
    существует, это должен быть пустой каталог.
    """
    if source is not None and is_inside(path, source):
        raise VfsError(
            f"cannot save VFS: {path} is the source directory or inside it"
        )
    if not os.path.lexists(path):
        return
    if not os.path.isdir(path):
        raise VfsError(
            f"cannot save VFS: {path} already exists and is not a directory"
        )
    if os.listdir(path):
        raise VfsError(f"cannot save VFS: directory {path} is not empty")


class Vfs:
    """Файловая система в памяти: дерево каталогов и файлов."""

    def __init__(self, root: VfsDir, source: str | None = None) -> None:
        """Создаёт VFS с корнем root; source — каталог-источник на диске."""
        self.root = root
        self.source = source

    @classmethod
    def from_directory(cls, path: str) -> Vfs:
        """Загружает VFS из каталога на диске; сам каталог не меняется."""
        if not os.path.exists(path):
            raise VfsError(f"VFS not found: {path}")
        if not os.path.isdir(path):
            raise VfsError(f"invalid VFS format: not a directory: {path}")
        name = os.path.basename(os.path.abspath(path)) or os.sep
        return cls(read_directory(path, name), source=path)

    @classmethod
    def default(cls) -> Vfs:
        """Создаёт VFS по умолчанию в памяти."""
        return cls(make_default_root())

    def count(self) -> tuple[int, int]:
        """Возвращает число каталогов (без корня) и число файлов."""
        return count_nodes(self.root)

    def save(self, path: str) -> None:
        """Сохраняет текущее состояние VFS на диск в виде дерева каталогов.

        Формат совпадает с исходным: каталоги и файлы с теми же именами.
        """
        try:
            check_save_target(path, self.source)
            os.makedirs(path, exist_ok=True)
            write_directory(self.root, path)
        except OSError as exc:
            raise disk_error("save VFS to", path, exc) from exc

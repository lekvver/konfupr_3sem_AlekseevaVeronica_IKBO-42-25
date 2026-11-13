"""Вспомогательные функции для тестов."""

import contextlib
import io
import os
import tempfile
from typing import Iterator, List, Tuple

from depgraph.cli import main


def run_main(argv: List[str]) -> Tuple[int, str, str]:
    """Вызывает main с перехватом вывода: код, stdout, stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


@contextlib.contextmanager
def temp_file(text: str, name: str = "repo.txt") -> Iterator[str]:
    """Создаёт временный файл с текстом и возвращает путь к нему."""
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        yield path

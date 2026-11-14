"""Получение SVG-изображения из текста D2 внешней программой d2."""

import os
import subprocess

from depgraph.errors import RenderError

D2_ENV = "DEPGRAPH_D2"
D2_DEFAULT = "d2"
INSTALL_URL = "https://d2lang.com/tour/install"
TIMEOUT_SECONDS = 120


def d2_command() -> str:
    """Имя программы d2 (его можно заменить переменной DEPGRAPH_D2)."""
    return os.environ.get(D2_ENV, D2_DEFAULT)


def render_svg(d2_path: str, svg_path: str) -> None:
    """Запускает «d2 файл.d2 файл.svg»; при сбое возбуждает RenderError."""
    command = d2_command()
    try:
        result = subprocess.run(
            [command, d2_path, svg_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise RenderError(
            f"program {command!r} not found; install D2: {INSTALL_URL}"
        ) from error
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RenderError(f"cannot run {command!r}: {error}") from error
    if result.returncode != 0:
        raise RenderError(f"d2 failed: {result.stderr.strip()}")

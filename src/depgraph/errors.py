"""Исключения инструмента."""


class DepGraphError(Exception):
    """Ошибка, текст которой показывается пользователю как есть."""


class ConfigError(DepGraphError):
    """Неверные параметры командной строки."""


class RepositoryError(DepGraphError):
    """Ошибка загрузки или разбора репозитория."""


class PackageNotFoundError(RepositoryError):
    """Запрошенного пакета нет в репозитории."""


class GraphError(DepGraphError):
    """Ошибка построения или обработки графа зависимостей."""


class RenderError(DepGraphError):
    """Не удалось получить изображение графа."""

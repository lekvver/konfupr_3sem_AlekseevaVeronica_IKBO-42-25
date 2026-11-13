"""Общий интерфейс репозиториев: реального (apt) и тестового."""

from typing import List, Protocol, Tuple


class Repository(Protocol):
    """Источник сведений о пакетах и их прямых зависимостях."""

    def has_package(self, name: str) -> bool:
        """Есть ли в репозитории пакет с таким именем."""

    def version(self, name: str) -> str:
        """Версия пакета (у тестового репозитория пустая строка)."""

    def is_known(self, name: str) -> bool:
        """Известно ли имя репозиторию."""

    def dependency_groups(self, name: str) -> List[Tuple[str, Tuple[str, ...]]]:
        """Прямые зависимости: (выбранный пакет, группа альтернатив)."""

    def dependencies(self, name: str) -> List[str]:
        """Имена прямых зависимостей без повторов."""

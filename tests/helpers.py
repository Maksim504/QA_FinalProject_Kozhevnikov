"""Общие вспомогательные функции для тестов."""

import time

MARKER = "QA_auto"


def unique_name() -> str:
    """Уникальное имя для создаваемых объектов."""
    return f"{MARKER}_тест_{int(time.time() * 1000)}"


def unique_title(text: str) -> str:
    """Уникальный заголовок плана для изоляции тестов."""
    return f"{MARKER} {text} {int(time.time() * 1000)}"
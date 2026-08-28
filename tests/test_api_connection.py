"""API: проверка соединения с сервером."""

import pytest

pytestmark = pytest.mark.api


def test_connection_ok(api_client):
    """Проверяет, что соединение с API устанавливается."""
    assert api_client.test_connection() is True
"""API: получение списка типов питания."""

import pytest

pytestmark = pytest.mark.api


def test_get_meal_types_returns_list(api_client):
    """Список типов питания не пуст."""
    meal_types = api_client.get_meal_types()
    assert isinstance(meal_types, list)
    assert len(meal_types) > 0
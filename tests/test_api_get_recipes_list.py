"""API: get_recipes() возвращает список рецептов."""

import pytest

pytestmark = pytest.mark.api


def test_get_recipes_returns_list(api_client):
    """get_recipes() возвращает список."""
    recipes = api_client.get_recipes()
    assert isinstance(recipes, list)
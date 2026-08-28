"""API: создание рецепта."""

import pytest

from tests.helpers import unique_name

pytestmark = pytest.mark.api


def test_create_recipe(api_client):
    """Создание рецепта через API: проверка id и имени."""
    name = unique_name()
    recipe = api_client.create_recipe({"name": name})
    try:
        assert recipe.get("id") is not None
        assert recipe.get("name") == name
        assert api_client.recipe_exists(recipe["id"])
    finally:
        api_client.delete_recipe(recipe["id"])
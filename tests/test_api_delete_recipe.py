"""API: удаление рецепта."""

import pytest

from tests.helpers import unique_name

pytestmark = pytest.mark.api


def test_delete_recipe(api_client):
    """Удаление рецепта: после удаления рецепт не возвращается в списке."""
    recipe = api_client.create_recipe({"name": unique_name()})
    api_client.delete_recipe(recipe["id"])
    assert not api_client.recipe_exists(recipe["id"])
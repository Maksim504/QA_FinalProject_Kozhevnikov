"""API: создание рецепта с ингредиентами."""

import pytest

from tests.helpers import unique_name

pytestmark = pytest.mark.api


def test_create_recipe_with_ingredients(api_client):
    """Рецепт создаётся вместе с ингредиентами (food/unit создаются автоматически)."""
    payload = {
        "name": unique_name(),
        "steps": [
            {
                "ingredients": [
                    {"food": {"name": "Тестовый продукт"}, "amount": 1, "unit": {"name": "шт"}}
                ]
            }
        ],
    }
    recipe = api_client.create_recipe(payload)
    try:
        steps = recipe.get("steps", [])
        assert steps, "У созданного рецепта должны быть шаги"
        assert steps[0].get("ingredients"), "У шага должны быть ингредиенты"
        food = steps[0]["ingredients"][0]["food"]
        assert food.get("name") == "Тестовый продукт"
    finally:
        api_client.delete_recipe(recipe["id"])
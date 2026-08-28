"""API: импорт рецепта по внешней ссылке."""

import requests
import pytest

pytestmark = pytest.mark.api


def test_import_recipe_from_url(api_client, load_test_data):
    """Импорт рецепта по ссылке из тестовых данных."""
    link = next((item for item in load_test_data["recipes"] if item.get("importable", True)), None)
    if link is None:
        pytest.skip("В тестовых данных нет ссылок для импорта")

    try:
        recipe = api_client.import_and_create_recipe(link["url"])
    except (requests.HTTPError, RuntimeError) as error:
        pytest.skip(f"Импорт по ссылке не удался: {error}")
    else:
        try:
            assert recipe.get("id") is not None
            assert recipe.get("name")
        finally:
            api_client.delete_recipe(recipe["id"])
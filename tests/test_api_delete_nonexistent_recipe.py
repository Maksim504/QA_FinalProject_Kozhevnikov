"""API: обработка ошибки при удалении несуществующего рецепта."""

import requests
import pytest

pytestmark = pytest.mark.api


def test_delete_nonexistent_recipe_raises(api_client):
    """Удаление несуществующего рецепта должно вызывать ошибку."""
    with pytest.raises((requests.HTTPError, RuntimeError)):
        api_client.delete_recipe(999999999)
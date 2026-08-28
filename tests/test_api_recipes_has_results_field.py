"""API: список рецептов содержит поле results."""

import pytest

pytestmark = pytest.mark.api


def test_get_recipes_has_results_field(api_client):
    """Список рецептов должен содержать поле `results` (объект пагинации)."""
    raw = api_client._make_request("GET", "/api/recipe/", expected_status=(200,))
    assert "results" in raw
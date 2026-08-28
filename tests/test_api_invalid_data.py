"""API: обработка невалидных данных (валидация сервера)."""

import requests
import pytest

pytestmark = pytest.mark.api


def test_create_recipe_invalid_data_returns_400(api_client):
    """Невалидный рецепт (без обязательного поля name) отклоняется с кодом 400.

    create_recipe подставляет steps=[] по умолчанию, поэтому в запросе
    остаётся только пустой steps, а поле name отсутствует — сервер
    отвечает 400, рецепт не создаётся.
    """
    with pytest.raises(requests.HTTPError) as exc_info:
        api_client.create_recipe({})
    assert exc_info.value.response.status_code == 400
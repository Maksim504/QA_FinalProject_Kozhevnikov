"""API: создание и удаление плана питания."""

from datetime import datetime

import pytest

import utils.generate_test_data as test_data

pytestmark = pytest.mark.api


def test_create_and_delete_meal_plan(api_client, get_or_create_recipe):
    """Создание плана питания, получение по id и удаление."""
    meal_type = api_client.get_meal_type_by_name("Завтрак") or api_client.get_meal_types()[0]
    now = datetime.now()

    payload = test_data.prepare_meal_plan_payload(
        recipe=get_or_create_recipe,
        meal_type=meal_type,
        from_date=now,
        to_date=now,
        servings=2,
        addshopping=False,
    )
    meal_plan = api_client.create_meal_plan(**payload)
    try:
        assert meal_plan.get("id") is not None
        fetched = api_client.get_meal_plan_by_id(meal_plan["id"])
        assert fetched.get("id") == meal_plan["id"]
        assert fetched.get("servings") == 2
    finally:
        api_client.delete_meal_plan(meal_plan["id"])
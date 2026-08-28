"""UI: просмотр Meal Plan на календаре."""

from datetime import datetime

import allure
import pytest

import utils.generate_test_data as test_data
from pages.meal_plan_page import MealPlanPage
from tests.helpers import MARKER, unique_title

pytestmark = pytest.mark.ui


@allure.step("Просмотр плана питания на календаре")
def test_view_meal_plan_ui(authorized_driver, base_url, api_client, get_or_create_recipe, cleanup_qa_auto, ui_username):
    """
    Сценарий: созданный через API план отображается на календаре
    (карточка с названием рецепта), данные доступны через API.
    """
    recipe = get_or_create_recipe
    meal_type = api_client.get_meal_type_by_name("Завтрак") or api_client.get_meal_types()[0]
    from_date = to_date = datetime.now()

    with allure.step("Создать план через API для проверки отображения"):
        payload = test_data.prepare_meal_plan_payload(
            recipe=recipe, meal_type=meal_type,
            from_date=from_date, to_date=to_date,
            servings=1, title=unique_title("UI просмотр"), addshopping=False,
        )
        plan = api_client.create_meal_plan(**payload)

    try:
        with allure.step("Открыть календарь и найти карточку"):
            mp = MealPlanPage(authorized_driver, base_url).open_meal_plan_page()
            assert mp.is_authorized(ui_username)
            card = mp.find_card_by_text(recipe["name"])
            assert recipe["name"] in card.text, (
                f"Название рецепта '{recipe['name']}' не отображается в карточке"
            )

        with allure.step("Проверить план через API по его id"):
            fetched = api_client.get_meal_plan_by_id(plan["id"])
            assert fetched.get("id") == plan["id"]
            assert (fetched.get("title") or "").startswith(MARKER)
    finally:
        api_client.delete_meal_plan(plan["id"])
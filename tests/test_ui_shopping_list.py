"""UI: список покупок формируется из Meal Plan."""

from datetime import datetime

import allure
import pytest

import utils.generate_test_data as test_data
from pages.shopping_list_page import ShoppingListPage
from tests.helpers import unique_title

pytestmark = pytest.mark.ui


@allure.step("Проверка списка покупок, сформированного из плана питания")
def test_shopping_list_from_meal_plan(authorized_driver, base_url, api_client, cleanup_qa_auto):
    """
    Сценарий: создаём рецепт с ингредиентом и план с флагом addshopping,
    открываем «Лист покупок» и убеждаемся, что ингредиент появился.
    """
    food_name = "Морковь тестовая"

    with allure.step("Создать рецепт с ингредиентом через API"):
        recipe = api_client.create_recipe({
            "name": unique_title("рецепт для покупок"),
            "steps": [{
                "ingredients": [{"food": {"name": food_name}, "amount": 6, "unit": {"name": "кг"}}],
            }],
        })

    meal_type = api_client.get_meal_type_by_name("Завтрак") or api_client.get_meal_types()[0]

    with allure.step("Создать план с addshopping=True (товар попадёт в список)"):
        payload = test_data.prepare_meal_plan_payload(
            recipe={"id": recipe["id"], "name": recipe["name"], "keywords": []},
            meal_type=meal_type,
            from_date=datetime.now(), to_date=datetime.now(),
            servings=1, title=unique_title("UI покупки"), addshopping=True,
        )
        plan = api_client.create_meal_plan(**payload)

    try:
        with allure.step("Открыть /shopping и проверить наличие ингредиента"):
            sl = (
                ShoppingListPage(authorized_driver, base_url)
                .open_shopping_list()
                .wait_loaded()
            )
            assert sl.has_entry_with(food_name), (
                f"Ингредиент '{food_name}' не найден в списке покупок"
            )

        with allure.step("Проверить через API наличие позиций листа покупок"):
            entries = api_client.get_shopping_list()
            assert entries, "API вернул пустой список покупок"

        with allure.step("Очистить лист покупок через UI-кнопку не требуется: очищаем API"):
            pass  # итоговая очистка выполняется в cleanup_qa_auto
    finally:
        api_client.delete_meal_plan(plan["id"])
        try:
            api_client.delete_recipe(recipe["id"])
        except Exception:
            pass
"""UI: удаление Meal Plan и проверка через API."""

import time
from datetime import datetime

import allure
import pytest

import utils.generate_test_data as test_data
from pages.meal_plan_dialog import MealPlanDialog
from pages.meal_plan_page import MealPlanPage
from tests.helpers import unique_title

pytestmark = pytest.mark.ui


@allure.step("Удаление плана питания через UI + проверка через API")
def test_delete_meal_plan_ui_and_api(authorized_driver, base_url, api_client, get_or_create_recipe, cleanup_qa_auto, ui_username):
    """
    Сценарий: открываем диалог карточки плана, нажимаем «Удалить»;
    карточка пропадает с календаря, а через API план больше не возвращается.
    """
    recipe = get_or_create_recipe
    meal_type = api_client.get_meal_type_by_name("Завтрак") or api_client.get_meal_types()[0]

    with allure.step("Создать план через API, который будем удалять"):
        payload = test_data.prepare_meal_plan_payload(
            recipe=recipe, meal_type=meal_type,
            from_date=datetime.now(), to_date=datetime.now(),
            servings=1, title=unique_title("UI удаление"), addshopping=False,
        )
        plan = api_client.create_meal_plan(**payload)

    try:
        with allure.step("Открыть календарь и найти карточку плана"):
            mp = MealPlanPage(authorized_driver, base_url).open_meal_plan_page()
            card = mp.find_card_by_text(recipe["name"])

        with allure.step("Открыть диалог редактирования и нажать «Удалить»"):
            mp.open_edit_dialog(card)
            dialog = MealPlanDialog(authorized_driver, base_url)
            assert dialog.is_open(), "Диалог редактирования плана не открылся"
            dialog.click_delete()
            dialog.confirm_delete()

        with allure.step("Проверить, что карточка исчезла с календаря"):
            # ждём обновления календаря после удаления
            deadline = time.time() + 20
            removed = False
            while time.time() < deadline:
                if not mp.is_visible(mp.MEAL_PLAN_CARD, timeout=2):
                    removed = True
                    break
                time.sleep(1)
            # повторная загрузка страницы исключает кэш отображения
            mp.open_meal_plan_page()
            assert mp.get_plan_card_count() == 0, "Карточки плана остались на календаре после удаления"

        with allure.step("Проверить через API, что план удалён"):
            plans = api_client.get_meal_plan()
            assert all(p.get("id") != plan["id"] for p in plans), (
                f"План id={plan['id']} всё ещё возвращается API"
            )
    finally:
        api_client.delete_meal_plan(plan["id"])
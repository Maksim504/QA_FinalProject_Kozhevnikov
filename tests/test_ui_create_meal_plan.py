"""UI: создание Meal Plan через форму и проверка через API."""

import time

import allure
import pytest

from pages.meal_plan_dialog import MealPlanDialog
from pages.meal_plan_page import MealPlanPage
from tests.helpers import unique_title

pytestmark = pytest.mark.ui


@allure.step("Создание плана питания через UI")
def test_create_meal_plan_ui(authorized_driver, base_url, api_client, get_or_create_recipe, cleanup_qa_auto, ui_username):
    """
    Сценарий: через форму создания плана (клик по ячейке календаря)
    заполняем рецепт, тип блюда, количество порций и сохраняем.
    Проверяем появление карточки на календаре и запись через API.
    """
    recipe_name = get_or_create_recipe["name"]
    title = unique_title("UI создание")

    with allure.step("Открыть календарь и открыть диалог создания"):
        mp = MealPlanPage(authorized_driver, base_url).open_meal_plan_page()
        assert mp.is_authorized(ui_username), "Пользователь не авторизован"
        initial_cards = mp.get_plan_card_count()
        mp.open_create_dialog()

    with allure.step("Заполнить форму создания плана"):
        dialog = MealPlanDialog(authorized_driver, base_url)
        assert dialog.is_open(), "Диалог создания плана не открылся"
        dialog.select_recipe(recipe_name)
        dialog.select_meal_type("Завтрак")
        dialog.set_title(title)
        dialog.set_servings(2)
        dialog.set_note("Заполнено автотестом")

    with allure.step("Переключить чекбокс «Добавить в лист покупок»"):
        # состояние до клика берётся из настроек пользователя (может быть и True, и False),
        # поэтому кликаем один раз и запоминаем фактический результат для сверки с API
        expect_shopping = dialog.toggle_add_to_shopping()

    with allure.step("Нажать «Создать» и закрыть диалог"):
        dialog.click_create()
        # диалог остаётся открытым для повторного добавления (close-after-create=false)
        time.sleep(1)
        dialog.close()

    with allure.step("Проверить появление карточки плана на календаре"):
        # дожидаемся, пока API-данные отрисуют карточку
        deadline = time.time() + 20
        card = None
        while time.time() < deadline:
            try:
                card = mp.find_card_by_text(recipe_name)
                break
            except AssertionError:
                time.sleep(1)
        assert card is not None, f"Карточка плана '{recipe_name}' не появилась на календаре"
        assert mp.get_plan_card_count() > initial_cards, (
            "Количество карточек не увеличилось после создания"
        )

    with allure.step("Проверить через API, что план создан"):
        plans = api_client.get_meal_plan()
        created = [p for p in plans if (p.get("title") or "") == title]
        assert created, f"План с заголовком '{title}' не найден через API"
        # чекбокс «Добавить в лист покупок» должен отразиться в поле shopping
        assert created[0].get("shopping") is expect_shopping, (
            f"Состояние чекбокса ({expect_shopping}) не совпало с API ({created[0].get('shopping')})"
        )
        # выбранные в UI порции должны сохраниться в плане
        assert created[0].get("servings") == 2, (
            f"Количество порций в API ({created[0].get('servings')}) не совпало с заданным (2)"
        )
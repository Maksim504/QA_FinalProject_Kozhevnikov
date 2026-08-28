"""Страница «Лист покупок» (Shopping List): /shopping."""

import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage


class ShoppingListPage(BasePage):
    """
    Лист покупок Tandoor.

    Каждая позиция — .v-list-item#id_sli_<id>.shopping-border:
    - количество и единица измерения: .text-no-wrap b;
    - название ингредиента: основной текст элемента;
    - источник: small.text-disabled (рецепт и тип блюда);
    - кнопка «куплено»: .btn-success (иконка fa-check).
    """

    SHOPPING_URL = "/shopping"

    ENTRY = (By.CSS_SELECTOR, ".v-list-item.shopping-border")
    ENTRY_AMOUNT = (By.CSS_SELECTOR, ".text-no-wrap b")
    ENTRY_ORIGIN = (By.CSS_SELECTOR, "small.text-disabled")
    BUY_BUTTON = (By.CSS_SELECTOR, ".btn-success")

    def __init__(self, driver: WebDriver, base_url: str = "") -> None:
        super().__init__(driver, base_url)

    @allure.step("Открыть страницу /shopping")
    def open_shopping_list(self) -> "ShoppingListPage":
        """Открывает лист покупок и ждёт его содержимого."""
        self.open(self.SHOPPING_URL)
        return self

    @allure.step("Проверить, что страница списка покупок доступна")
    def wait_loaded(self) -> "ShoppingListPage":
        """Ждёт появление списка покупок (контейнер позиций)."""
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(self.ENTRY)
        )
        return self

    @allure.step("Получить позиции списка покупок")
    def get_entries(self) -> list:
        """Возвращает элементы позиций товаров."""
        return self.driver.find_elements(*self.ENTRY)

    @allure.step("Проверить наличие товара «{food_name}» в списке")
    def has_entry_with(self, food_name: str, amount: str = "") -> bool:
        """
        Возвращает True, если в листе есть позиция с названием food_name
        и опционально количеством amount (например: "6 кг").
        """
        for entry in self.get_entries():
            text = entry.text
            if food_name in text and (not amount or amount in text):
                return True
        return False

    @allure.step("Получить текст первой позиции")
    def get_first_entry_text(self) -> str:
        entries = self.get_entries()
        assert entries, "Лист покупок пуст"
        return entries[0].text
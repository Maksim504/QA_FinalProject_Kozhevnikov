"""Страница «Планирование блюд» (Meal Plan): /mealplan."""

import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage
from pages.header_component import HeaderComponent
from pages.welcome_page import WelcomePage


class MealPlanPage(BasePage):
    """
    Календарь планов питания (vue-simple-calendar).

    - ячейка дня: .cv-day (сегодня: .cv-day.today), внутри .cv-day-number;
    - клик по .cv-day-number открывает диалог СОЗДАНИЯ плана;
    - карточка плана: .cv-item, текст показан в span.font-light;
      клик по тексту карточки открывает диалог РЕДАКТИРОВАНИЯ.
    """

    MEAL_PLAN_URL = "/mealplan"

    # Лениво подгружаемый чанк редактора MealPlan: без предзагрузки диалог
    # создания открывается и тут же закрывается пустым.
    EDITOR_CHUNK_PATH = "/static/vue3/assets/MealPlanEditor-CF1QHkdK.js"

    # Календарь
    DAY_CELL = (By.CSS_SELECTOR, ".cv-day")
    TODAY_CELL = (By.CSS_SELECTOR, ".cv-day.today")
    DAY_NUMBER = (By.CSS_SELECTOR, ".cv-day-number")

    # Карточки планов питания
    MEAL_PLAN_CARD = (By.CSS_SELECTOR, ".cv-item")
    CARD_TEXT = (By.CSS_SELECTOR, ".cv-item span.font-light")  # текст-триггер диалога редактирования

    def __init__(self, driver: WebDriver, base_url: str = "") -> None:
        super().__init__(driver, base_url)

    @allure.step("Открыть страницу /mealplan")
    def open_meal_plan_page(self, dismiss_wizard: bool = True) -> "MealPlanPage":
        """Открывает календарь; при необходимости закрывает мастер /welcome."""
        self.open(self.MEAL_PLAN_URL)
        if dismiss_wizard and "welcome" in self.get_current_url():
            WelcomePage(self.driver, self.base_url).dismiss_if_present()
            self.open(self.MEAL_PLAN_URL)
        self._preload_editor_chunk()
        self.wait_for_visible(self.DAY_CELL)
        return self

    @allure.step("Предзагрузить чанк редактора диалога плана")
    def _preload_editor_chunk(self, timeout: int = 15) -> None:
        """
        Подгружает async-модуль MealPlanEditor до открытия диалога.

        Без этого клик по дню открывает пустой диалог, который сразу
        закрывается (ленивая загрузка чанка не успевает завершиться).
        """
        import time

        url = f"{self.base_url}{self.EDITOR_CHUNK_PATH}"
        self.driver.execute_script(
            "if (window.__editChunkLoaded) return true;"
            "var s=document.createElement('script');s.type='module';"
            "s.textContent=`import('" + url
            + "').then(()=>{window.__editChunkLoaded=true;}).catch(e=>{window.__editChunkError=String(e);});`;"
            "document.head.appendChild(s); return false;"
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.driver.execute_script("return window.__editChunkLoaded === true"):
                return
            time.sleep(0.3)
        raise AssertionError("Чанк редактора диалога не загрузился")

    # ------------------------------------------------------------------
    # Календарь
    # ------------------------------------------------------------------
    @allure.step("Получить ячейку сегодняшнего дня")
    def get_today_cell(self) -> WebElement:
        """Возвращает ячейку сегодняшнего дня (последнюю из совпавших)."""
        cells = self.driver.find_elements(*self.TODAY_CELL)
        if cells:
            return cells[-1]
        return self.find_all(self.DAY_CELL)[10]

    @allure.step("Открыть диалог создания плана кликом по ячейке дня")
    def open_create_dialog(self) -> None:
        """Кликает по числу в ячейке дня — открывается диалог создания."""
        from selenium.webdriver.common.action_chains import ActionChains

        day = self.get_today_cell()
        target = day.find_element(*self.DAY_NUMBER)
        ActionChains(self.driver).move_to_element(target).click().perform()

    # ------------------------------------------------------------------
    # Карточки планов
    # ------------------------------------------------------------------
    @allure.step("Получить список карточек планов на странице")
    def get_plan_cards(self) -> list:
        """Возвращает список карточек .cv-item текущего отображаемого периода."""
        return self.driver.find_elements(*self.MEAL_PLAN_CARD)

    @allure.step("Получить количество карточек на странице")
    def get_plan_card_count(self) -> int:
        return len(self.get_plan_cards())

    @allure.step("Найти карточку плана по тексту {text}")
    def find_card_by_text(self, text: str) -> WebElement:
        """Ищет карточку, в тексте которой встречается подстрока text."""
        for card in self.get_plan_cards():
            if text in card.text:
                return card
        raise AssertionError(f"Карточка с текстом '{text}' не найдена на странице")

    @allure.step("Открыть диалог редактирования плана кликом по тексту карточки")
    def open_edit_dialog(self, card: WebElement) -> None:
        """Кликает по тексту карточки — открывается диалог редактирования."""
        from selenium.webdriver.common.action_chains import ActionChains

        text_el = card.find_element(*self.CARD_TEXT)
        ActionChains(self.driver).move_to_element(text_el).click().perform()

    @allure.step("Проверить, что пользователь авторизован")
    def is_authorized(self, username: str) -> bool:
        """Проверяет наличие имени пользователя в навигационном меню."""
        return HeaderComponent(self.driver, self.base_url).is_authorized(username)
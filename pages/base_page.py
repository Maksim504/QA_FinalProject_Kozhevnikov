"""Базовый класс page-object с общими Selenium-методами."""

import time
from typing import List

from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[By, str]


class BasePage:
    """Общие методы для всех страниц: открыть URL, найти элемент, кликнуть, заполнить поле."""

    DEFAULT_TIMEOUT = 15

    def __init__(self, driver: WebDriver, base_url: str = "") -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Навигация
    # ------------------------------------------------------------------
    def open(self, path: str = "/") -> "BasePage":
        """Открывает URL = base_url + path."""
        self.driver.get(f"{self.base_url}{path}")
        return self

    def get_current_url(self) -> str:
        """Возвращает текущий URL страницы."""
        return self.driver.current_url

    # ------------------------------------------------------------------
    # Поиск элементов
    # ------------------------------------------------------------------
    def find(self, locator: Locator, timeout: int = DEFAULT_TIMEOUT) -> WebElement:
        """Ждёт появления элемента в DOM и возвращает его."""
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))

    def find_all(self, locator: Locator, timeout: int = DEFAULT_TIMEOUT) -> List[WebElement]:
        """Ждёт появления хотя бы одного элемента и возвращает список."""
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
        return self.driver.find_elements(*locator)

    def wait_for_visible(self, locator: Locator, timeout: int = DEFAULT_TIMEOUT) -> WebElement:
        """Ждёт, пока элемент станет видимым, и возвращает его."""
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))

    def is_visible(self, locator: Locator, timeout: int = 10) -> bool:
        """Возвращает True, если элемент видим в течение timeout."""
        try:
            self.wait_for_visible(locator, timeout=timeout)
            return True
        except Exception:
            return False

    def click(self, locator: Locator, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Ждёт кликабельности элемента, прокручивает к нему и кликает.

        Vue-приложение иногда не успевает отрисовать макет: элемент перекрывается
        соседним полем. Поэтому при перехвате клика повторяем его несколько раз,
        в крайнем случае кликаем через JavaScript.
        """
        element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        for attempt in range(3):
            try:
                element.click()
                return
            except ElementClickInterceptedException:
                time.sleep(0.4)
        self.driver.execute_script("arguments[0].click();", element)

    def type_text(self, locator: Locator, value: str, clear: bool = True) -> None:
        """Заполняет текстовое поле; при clear=True предварительно очищает его."""
        element = self.find(locator)
        if clear:
            element.clear()
        element.send_keys(value)

    def get_text(self, locator: Locator, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Возвращает текст элемента."""
        return self.find(locator, timeout=timeout).text

    # ------------------------------------------------------------------
    # Прочее
    # ------------------------------------------------------------------
    def save_screenshot(self, path: str) -> None:
        """Сохраняет скриншот текущего состояния страницы."""
        self.driver.save_screenshot(path)
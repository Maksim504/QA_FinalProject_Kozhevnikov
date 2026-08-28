"""Страница-мастер первичной настройки Tandoor: /welcome."""

import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage


class WelcomePage(BasePage):
    """
    Мастер первичной настройки аккаунта.

    Впервые вошедший пользователь вместо /mealplan попадает на /welcome
    с кнопками «Skip» и «Следующий». Мастер закрывается кнопкой Skip.
    """

    WELCOME_URL = "/welcome"
    SKIP_BUTTON = (By.XPATH, "//button[contains(.,'Skip')]")
    NEXT_BUTTON = (By.XPATH, "//button[contains(.,'Следующий') or contains(.,'Далее')]")

    def __init__(self, driver: WebDriver, base_url: str = "") -> None:
        super().__init__(driver, base_url)

    @allure.step("Пропустить мастер первичной настройки")
    def dismiss_if_present(self, max_clicks: int = 3) -> bool:
        """
        Нажимает «Skip», пока мастер виден. Возвращает True, если мастер закрыли.
        """
        clicked = False
        for _ in range(max_clicks):
            if "welcome" not in self.get_current_url():
                return clicked
            skip = self.driver.find_elements(*self.SKIP_BUTTON)
            nxt = self.driver.find_elements(*self.NEXT_BUTTON)
            if skip:
                skip[0].click()
                clicked = True
            elif nxt:
                nxt[0].click()
                clicked = True
            else:
                return clicked
        return clicked

    @allure.step("Открыть страницу мастера /welcome")
    def open_welcome(self) -> "WelcomePage":
        """Открывает /welcome (нужно для закрытия мастера)."""
        self.open(self.WELCOME_URL)
        return self
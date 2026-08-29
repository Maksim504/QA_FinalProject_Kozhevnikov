"""Страница авторизации Tandoor (Django/allauth): /accounts/login/."""

import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage
from pages.welcome_page import WelcomePage


class LoginPage(BasePage):
    """
    Логин-страница (форма входа).

    Поле логина ожидает USERNAME (не email): TANDOOR_UI_USERNAME=Максим.
    После входа приложение переводит пользователя на главную страницу.
    """

    LOGIN_URL = "/accounts/login/"
    USERNAME_FIELD = (By.ID, "id_login")
    PASSWORD_FIELD = (By.ID, "id_password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button.btn-success")

    def __init__(self, driver: WebDriver, base_url: str = "") -> None:
        super().__init__(driver, base_url)

    @allure.step("Открыть страницу авторизации")
    def open_login_page(self) -> "LoginPage":
        """Открывает форму входа."""
        self.open(self.LOGIN_URL)
        self.wait_for_visible(self.USERNAME_FIELD)
        return self

    def login(self, username: str, password: str) -> "LoginPage":
        """Заполняет форму ({username}) и нажимает «Войти».

        Шаг оформлен через контекстный менеджер, чтобы пароль не попадал
        в параметры Allure-отчёта (отчёт публикуется на GitHub Pages).
        """
        with allure.step(f"Выполнить вход под пользователем '{username}'"):
            self.type_text(self.USERNAME_FIELD, username, clear=False)
            self.type_text(self.PASSWORD_FIELD, password, clear=False)
            self.click(self.SUBMIT_BUTTON)
        return self

    @allure.step("Дождаться окончания авторизации")
    def wait_login_done(self, timeout: int = 30) -> "LoginPage":
        """Ждёт ухода с логин-страницы (перенаправления после входа)."""
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if "/accounts/login" not in self.get_current_url():
                return self
            time.sleep(0.5)
        raise AssertionError("Авторизация не выполнена: страница логина не сменилась")

    @allure.step("Проверить, что открыта форма входа")
    def is_login_page(self) -> bool:
        """Возвращает True, если видима форма входа."""
        return self.is_visible(self.USERNAME_FIELD, timeout=5)

    @allure.step("Пройти мастер первичной настройки, если он открылся")
    def dismiss_welcome_wizard(self) -> "LoginPage":
        """Завершает первичный мастер (/welcome), если он перехватил переход."""
        WelcomePage(self.driver, self.base_url).dismiss_if_present()
        return self
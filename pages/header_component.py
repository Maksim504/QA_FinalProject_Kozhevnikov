"""Компонент верхней панели навигации (Header) и левого навигационного меню."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage


class HeaderComponent(BasePage):
    """Элементы верхней панели навигации Tandoor."""

    # Верхняя панель (v-app-bar): меню пользователя в виде аватара
    USER_MENU_AVATAR = (By.CSS_SELECTOR, ".v-app-bar .v-avatar")

    # Левое навигационное меню (v-navigation-drawer) — ссылки роутера
    MEAL_PLAN_LINK = (By.CSS_SELECTOR, 'a[href="/mealplan"]')
    SHOPPING_LINK = (By.CSS_SELECTOR, 'a[href="/shopping"]')
    IMPORT_LINK = (By.CSS_SELECTOR, 'a[href="/recipe/import"]')
    SETTINGS_LINK = (By.CSS_SELECTOR, 'a[href^="/settings"]')
    LOGOUT_LINK = (By.CSS_SELECTOR, 'a[href*="/logout"]')

    # Имя пользователя в левом меню (MenuUserInfo -> v-list-item-title)
    USER_NAME_IN_DRAWER = (By.CSS_SELECTOR, ".v-navigation-drawer .v-list-item-title")

    def __init__(self, driver: WebDriver, base_url: str = "") -> None:
        super().__init__(driver, base_url)

    def goto_meal_plan(self) -> None:
        """Переходит к разделу Meal Plan (/mealplan)."""
        self.click(self.MEAL_PLAN_LINK)

    def goto_shopping_list(self) -> None:
        """Переходит к разделу Shopping List (/shopping)."""
        self.click(self.SHOPPING_LINK)

    def open_user_menu(self) -> None:
        """Открывает выпадающее меню пользователя (клик по аватару)."""
        self.click(self.USER_MENU_AVATAR)

    def get_username_in_drawer(self) -> str:
        """Возвращает имя пользователя из левого навигационного меню."""
        return self.get_text(self.USER_NAME_IN_DRAWER)

    def is_authorized(self, username: str) -> bool:
        """
        Проверяет авторизацию по наличию имени пользователя в навигационном меню.
        Мощный селектор: ищет любой элемент, текст которого равен username.
        """
        return self.is_visible(self._text_locator(username), timeout=10)

    def logout(self) -> None:
        """Открывает меню пользователя и выходит из аккаунта."""
        self.open_user_menu()
        self.click(self.LOGOUT_LINK)

    @staticmethod
    def _text_locator(text: str):
        """Динамический локатор поиска элемента с точным текстом."""
        return (By.XPATH, f"//*[normalize-space(.)='{text}']")
"""UI: вход в приложение через форму авторизации."""

import allure
import pytest

from pages.header_component import HeaderComponent
from pages.login_page import LoginPage

pytestmark = pytest.mark.ui


@allure.step("Вход в приложение")
def test_ui_login(driver, base_url, ui_username, ui_password):
    """
    Сценарий: форма входа Tandoor принимает username/пароль,
    после входа в навигации отображается имя пользователя.
    """
    # очищаем cookies, чтобы гарантированно попасть на форму входа
    driver.delete_all_cookies()

    with allure.step("Открыть страницу авторизации и ввести данные"):
        from pages.welcome_page import WelcomePage

        login_page = (
            LoginPage(driver, base_url)
            .open_login_page()
            .login(ui_username, ui_password)
            .wait_login_done()
        )
        # после первого входа может открыться мастер /welcome
        WelcomePage(driver, base_url).dismiss_if_present()
        assert not login_page.is_login_page(), "Остались на странице входа"

    with allure.step("Проверить, что в меню отобразилось имя пользователя"):
        assert HeaderComponent(driver, base_url).is_authorized(ui_username), (
            f"Имя '{ui_username}' не найдено в навигации после входа"
        )
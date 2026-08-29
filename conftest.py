"""Глобальные фикстуры и хуки (Задания №2 и №3).

- api_client: экземпляр API-клиента;
- load_test_data: тестовые данные из data/recipes.json;
- get_or_create_recipe: существующий рецепт или создание нового через API;
- driver: WebDriver Chrome (headless локально, удалённый Selenium в CI);
- authorized_driver: авторизованный driver (восстановление cookies / вход);
- pytest_runtest_makereport: сохранение скриншота при падении теста.
"""

import json
import os

import pytest

import utils.generate_test_data as test_data
from api.client import TandoorAPIClient

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(PROJECT_ROOT, "data", "recipes.json")
COOKIES_FILE = os.path.join(PROJECT_ROOT, "data", "cookies.json")


def _load_cookies() -> list:
    """Читает сохранённые cookie из JSON-файла."""
    if not os.path.exists(COOKIES_FILE):
        return []
    with open(COOKIES_FILE, encoding="utf-8") as file:
        return json.load(file)


def _save_cookies(driver) -> None:
    """Сохраняет cookie браузера в JSON-файл для повторных входов."""
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
    with open(COOKIES_FILE, "w", encoding="utf-8") as file:
        json.dump(driver.get_cookies(), file, ensure_ascii=False, indent=2)
    print(f"\n[COOKIES] сохранены: {COOKIES_FILE}")


def _csrf_works(driver, tries: int = 2) -> bool:
    """
    Проверяет, что восстановленная сессия может выполнять изменяющие запросы.

    Выполняет пустой POST на /api/meal-plan/: ответ 400 (ошибка валидации)
    означает, что CSRF-проверка пройдена; 403 — что сессия/токен устарели.
    Один из ответов сервера может быть ложным сбоем (разные воркеры),
    поэтому опрос выполняется несколько раз.
    """
    js = (
        "const done=arguments[arguments.length-1];"
        "(async()=>{const m=document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);"
        "const token=m?m[1]:null;try{"
        "const r=await fetch('/api/meal-plan/',{method:'POST',"
        "headers:{'Content-Type':'application/json','X-Csrftoken':token},body:'{}'});"
        "done({status:r.status});}catch(e){done({status:0,error:String(e)});}})();"
    )
    driver.set_script_timeout(15000)
    results = []
    for _ in range(max(1, tries)):
        try:
            result = driver.execute_async_script(js) or {}
            results.append(result.get("status"))
        except Exception:
            results.append(0)
    return all(s not in (403, 0) for s in results) if results else False


def _fresh_login(driver, base_url: str, username: str, password: str, tries: int = 4) -> None:
    """
    Полноценный вход через форму: повторяется, т.к. POST логина на этом
    сервере иногда получает ложный CSRF-403.
    """
    from pages.login_page import LoginPage
    from pages.welcome_page import WelcomePage

    last_errors: list[str] = []
    for attempt in range(1, tries + 1):
        driver.delete_all_cookies()
        login_page = LoginPage(driver, base_url).open_login_page()
        login_page.login(username, password)
        try:
            login_page.wait_login_done(timeout=20)
            WelcomePage(driver, base_url).dismiss_if_present()
            print(f"[LOGIN] попытка {attempt} успешна")
            return
        except AssertionError:
            last_errors = [
                el.text.strip()
                for el in driver.find_elements("css selector", ".alert, .errorlist, [role=alert]")
                if el.text.strip()
            ]
            print(f"[LOGIN] попытка {attempt} не удалась, url={driver.current_url}")
    raise AssertionError(
        f"Свежий вход не удался за {tries} попыток: url={driver.current_url}, ошибки={last_errors[:3]}"
    )


@pytest.fixture(scope="session")
def api_client() -> TandoorAPIClient:
    """Создаёт экземпляр API-клиента и проверяет соединение."""
    client = TandoorAPIClient()
    assert client.test_connection(), "Нет соединения с API Tandoor"
    return client


@pytest.fixture(scope="session")
def base_url() -> str:
    """Базовый URL приложения из .env."""
    return os.getenv("BASE_URL", "https://tandoor.vs1.srv.eduson.tv").rstrip("/")


@pytest.fixture(scope="session")
def ui_username() -> str:
    """Логин (username) для UI-входа; в .env: TANDOOR_UI_USERNAME."""
    return os.getenv("TANDOOR_UI_USERNAME", "Максим")


@pytest.fixture(scope="session")
def ui_password() -> str:
    """Пароль для UI-входа из .env: TANDOOR_PASSWORD."""
    return os.getenv("TANDOOR_PASSWORD", "")


@pytest.fixture(scope="session")
def load_test_data() -> dict:
    """Загружает тестовые данные (ссылки на рецепты) из JSON-файла."""
    with open(DATA_FILE, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def get_or_create_recipe(api_client, load_test_data) -> dict:
    """
    Возвращает рецепт для тестов: берёт существующий или создаёт новый.

    Созданные в этой сессии рецепты (имя начинается с QA_auto)
    удаляются после завершения сессии.
    """
    recipe = test_data.get_or_create_recipe_for_tests(api_client, config=load_test_data)
    yield recipe

    for item in api_client.get_recipes():
        if item.get("name", "").startswith(test_data.MARKER):
            api_client.delete_recipe(item["id"])


@pytest.fixture(scope="session")
def driver(base_url):
    """
    WebDriver: headless Chrome локально.

    По умолчанию браузер запускается в headless-режиме; чтобы увидеть окно,
    задайте переменную окружения HEADLESS=0.

    В CI (переменная окружения CI) подключается к удалённому Selenium
    (адрес читается из SELENIUM_REMOTE_URL) — реализация для Задания №4.
    """
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    if os.getenv("HEADLESS", "1") != "0":
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=1720,1100")
    options.add_argument("--lang=ru-RU")

    if os.getenv("CI"):
        remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")
        browser = webdriver.Remote(command_executor=remote_url, options=options)
    else:
        browser = webdriver.Chrome(options=options)

    browser.implicitly_wait(5)
    browser.set_page_load_timeout(60)
    yield browser
    browser.quit()


@pytest.fixture(scope="session")
def authorized_driver(driver, base_url, ui_username, ui_password):
    """
    Авторизованный WebDriver.

    Сначала пробует восстановить сохранённые cookies (быстрый вход без формы),
    при неудаче выполняет полноценный вход через логин-страницу
    и сохраняет cookies для следующих запусков.
    """
    from pages.header_component import HeaderComponent

    driver.get(base_url)
    cookies = _load_cookies()

    if cookies:
        # применяем cookies и проверяем результат
        driver.get(base_url)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
        driver.get(base_url)
        try:
            if (
                "login" not in driver.current_url
                and HeaderComponent(driver, base_url).is_authorized(ui_username)
                and _csrf_works(driver, tries=2)
            ):
                print("[COOKIES] вход по сохранённым cookies")
                yield driver
                return
        except Exception:
            pass

    # полноценный вход со сбросом cookies (с ретраями, т.к. POST логина флаки)
    _fresh_login(driver, base_url, ui_username, ui_password)
    _save_cookies(driver)

    yield driver


@pytest.fixture(scope="function")
def cleanup_qa_auto(api_client):
    """
    Фикстура очистки тестовых данных после UI-теста плана питания.

    Удаляет планы с заголовком QA_auto и очищает список покупок.
    """
    yield
    test_data.cleanup_qa_auto_plans(api_client, clear_shopping=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Сохраняет скриншот в папку проекта, если тест упал."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver") or item.funcargs.get("authorized_driver")
        if driver is not None:
            try:
                screenshots_dir = os.path.join(PROJECT_ROOT, "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                path = os.path.join(screenshots_dir, f"{item.name}_{report.when}.png")
                driver.save_screenshot(path)
                print(f"\n[SCREENSHOT] сохранён: {path}")
            except Exception:  # скриншот не должен ломать отчёт
                pass
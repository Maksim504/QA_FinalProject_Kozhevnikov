"""Диалог создания/редактирования плана питания (ModelEditDialog)."""

import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage


class MealPlanDialog(BasePage):
    """
    Форма составления плана питания.

    Структура (проверено на боевом сервере):
    - «Рецепт»   — первая Vue-мультиселект (.multiselect-wrapper внутри диалога);
    - «Заголовок»— текстовое поле;
    - «Дата»/«Время» — заполняются автоматически выбранным днём;
    - «Тип блюда» — вторая Vue-мультиселект;
    - «Порции»   — числовое поле v-number-input;
    - «Заметка»  — textarea;
    - кнопка «Создать»/«Сохранить»/«Удалить» внизу карточки диалога.
    """

    # Диалог
    DIALOG = (By.CSS_SELECTOR, ".v-dialog .v-card")
    DIALOG_ACTIONS = (By.CSS_SELECTOR, ".v-card-actions")

    # Мультиселекты (рецепт — первый, тип блюда — второй).
    # Внимание: .multiselect-dropdown с опциями — СИБЛИНГ .multiselect-wrapper,
    # поэтому поиск опций ведётся внутри общего контейнера .multiselect.
    MULTISELECT = (By.CSS_SELECTOR, ".v-dialog .multiselect")
    MULTISELECT_SEARCH = (By.CSS_SELECTOR, ".multiselect-search")
    OPTION = (By.CSS_SELECTOR, ".multiselect-options li.multiselect-option")

    # Текстовые поля
    TITLE_FIELD = (By.XPATH, "//label[normalize-space(.)='Заголовок' and @for]/following-sibling::input")
    NOTE_FIELD = (By.XPATH, "//label[normalize-space(.)='Заметка' and @for]/following-sibling::textarea")
    SERVINGS_FIELD = (By.XPATH, "//label[normalize-space(.)='Порции' and @for]/following-sibling::input")

    # Чекбокс «Добавить в лист покупок» (появляется после выбора рецепта)
    ADD_TO_SHOPPING_INPUT = (
        By.XPATH,
        "//div[contains(@class,'v-dialog')]/descendant::input[@aria-label='Добавить в лист покупок']",
    )
    ADD_TO_SHOPPING_LABEL = (
        By.XPATH,
        "//div[contains(@class,'v-dialog')]/descendant::label[normalize-space(.)='Добавить в лист покупок']",
    )

    # Кнопки
    CREATE_BUTTON = (
        By.XPATH,
        "//div[contains(@class,'v-card-actions')]//button[contains(.,'Создать')]",
    )
    SAVE_BUTTON = (
        By.XPATH,
        "//div[contains(@class,'v-card-actions')]//button[contains(.,'Сохранить')]",
    )
    DELETE_BUTTON = (
        By.XPATH,
        "//div[contains(@class,'v-card-actions')]//button[contains(.,'Удалить')]",
    )

    # Диалог подтверждения удаления (DeleteConfirmDialog):
    # кнопка «Удалить» в карточке открывает дополнительный v-dialog
    # «Вы уверены, что хотите удалить этот объект?» с кнопками «ОТМЕНИТЬ»/«УДАЛИТЬ».
    CONFIRM_DELETE_DIALOG = (
        By.XPATH,
        "//div[contains(@class,'v-card')][contains(.,'Вы уверены')]",
    )
    CONFIRM_DELETE_BUTTON = (
        By.XPATH,
        "//div[contains(@class,'v-card')][contains(.,'Вы уверены')]//button[contains(.,'Удалить')]",
    )

    def __init__(self, driver: WebDriver, base_url: str = "") -> None:
        super().__init__(driver, base_url)

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------
    @allure.step("Проверить, что диалог открыт")
    def is_open(self) -> bool:
        return self.is_visible(self.DIALOG, timeout=5)

    @allure.step("Закрыть диалог (Esc)")
    def close(self) -> None:
        from selenium.webdriver.common.action_chains import ActionChains

        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    def _multiselect_search_input(self, index: int):
        """Возвращает поле поиска index-ого мультиселекта внутри диалога."""
        containers = self.driver.find_elements(*self.MULTISELECT)
        assert containers, "В диалоге не найдены мультиселекты"
        return containers[index].find_element(*self.MULTISELECT_SEARCH)

    @allure.step("Выбрать значение {visible_text} в мультиселекте #{index}")
    def _pick_option(self, index: int, visible_text: str, exact: bool = True) -> None:
        """Кликает по опции в выпадающем списке мультиселекта."""
        containers = self.driver.find_elements(*self.MULTISELECT)
        assert len(containers) > index, "Мультиселект не найден"
        container = containers[index]
        search = container.find_element(*self.MULTISELECT_SEARCH)
        search.click()
        search.send_keys(visible_text)

        # ждём появления опций и выбираем нужную
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(container, 15).until(
            EC.presence_of_element_located(self.OPTION)
        )
        options = container.find_elements(*self.OPTION)
        for option in options:
            label = option.get_attribute("aria-label") or option.text
            if (exact and label.strip() == visible_text) or (
                not exact and visible_text in label
            ):
                option.click()
                return
        # если строгого совпадения нет, берём первую опцию
        if options:
            options[0].click()

    # ------------------------------------------------------------------
    # Поля формы
    # ------------------------------------------------------------------
    @allure.step("Выбрать рецепт «{recipe_name}»")
    def select_recipe(self, recipe_name: str) -> None:
        """Вводит название рецепта в автокомплит и выбирает его из списка."""
        self._pick_option(0, recipe_name)

    @allure.step("Выбрать тип блюда «{meal_type}»")
    def select_meal_type(self, meal_type: str) -> None:
        """Выбирает тип питания в мультиселекте «Тип блюда»."""
        self._pick_option(1, meal_type)

    @allure.step("Задать заголовок плана «{title}»")
    def set_title(self, title: str) -> None:
        """Заполняет поле «Заголовок»."""
        self.type_text(self.TITLE_FIELD, title)

    @allure.step("Задать порции: {servings}")
    def set_servings(self, servings: int) -> None:
        """Заменяет значение поля «Порции» на servings."""
        element = self.find(self.SERVINGS_FIELD)
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(str(servings))

    @allure.step("Задать заметку «{note}»")
    def set_note(self, note: str) -> None:
        """Заполняет поле «Заметка»."""
        self.type_text(self.NOTE_FIELD, note)

    @allure.step("Проверить состояние чекбокса «Добавить в лист покупок»")
    def is_add_to_shopping_checked(self) -> bool:
        """Возвращает True, если чекбокс «Добавить в лист покупок» отмечен."""
        checked = self.find(self.ADD_TO_SHOPPING_INPUT).is_selected()
        print(f"[CHECKBOX] «Добавить в лист покупок» отмечен: {checked}")
        return checked

    @allure.step("Переключить чекбокс «Добавить в лист покупок»")
    def toggle_add_to_shopping(self) -> bool:
        """Кликает по чекбоксу и возвращает новое состояние (True = добавлен)."""
        import time

        self.click(self.ADD_TO_SHOPPING_LABEL)
        # даём Vue время отрисовать новое состояние
        time.sleep(0.3)
        return self.is_add_to_shopping_checked()

    # ------------------------------------------------------------------
    # Кнопки
    # ------------------------------------------------------------------
    @allure.step("Нажать «Создать»")
    def click_create(self) -> None:
        self.click(self.CREATE_BUTTON)

    @allure.step("Нажать «Сохранить»")
    def click_save(self) -> None:
        self.click(self.SAVE_BUTTON)

    @allure.step("Нажать «Удалить»")
    def click_delete(self) -> None:
        self.click(self.DELETE_BUTTON)

    @allure.step("Подтвердить удаление в диалоге подтверждения")
    def confirm_delete(self) -> None:
        """Клик по «Удалить» открывает подтверждение; этап подтверждает его."""
        self.wait_for_visible(self.CONFIRM_DELETE_DIALOG)
        self.click(self.CONFIRM_DELETE_BUTTON)
"""
TandoorAPIClient - клиент для работы с API Tandoor (https://tandoor.vs1.srv.eduson.tv/).

Хранит базовый URL и токен, выполняет запросы к REST API
и возвращает распарсенные JSON-ответы.

Задание №1: методы содержат только URL, тело запроса и минимальную
обработку ответа; вся остальная логика выносится в фикстуры/утилиты.

Использование:
    from api.client import TandoorAPIClient
    client = TandoorAPIClient()
    client.test_connection()
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Сервер нестабилен: при создании плана питания эпизодически возвращает 500.
MEAL_PLAN_CREATE_RETRIES = 5
MEAL_PLAN_RETRY_DELAY_SECONDS = 2


class TandoorAPIClient:
    """
    Клиент для взаимодействия с API Tandoor через Bearer-токен.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 40,
    ) -> None:
        """Сохраняет настройки подключения: базовый URL, токен, заголовки."""
        self.base_url = (base_url or os.getenv("BASE_URL", "https://tandoor.vs1.srv.eduson.tv")).rstrip("/")
        self.token = token or os.getenv("TANDOOR_TOKEN", "")
        self.username = username or os.getenv("TANDOOR_USERNAME", "")
        self.password = password or os.getenv("TANDOOR_PASSWORD", "")
        self.timeout = timeout

        if not self.token:
            raise ValueError("TANDOOR_TOKEN не задан. Проверьте .env")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Единый метод выполнения HTTP-запросов
    # ------------------------------------------------------------------
    def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expected_status: tuple = (200,),
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет HTTP-запрос к API и обрабатывает ошибки.

        :param method: HTTP-метод (GET, POST, PATCH, DELETE).
        :param path: путь вида "/api/recipe/".
        :param data: JSON-данные для POST/PATCH.
        :param params: query-параметры для GET.
        :param expected_status: кортеж допустимых кодов ответа.
        :return: распарсенный JSON или None для пустых ответов (204).
        :raises RuntimeError: при сетевой ошибке.
        :raises requests.HTTPError: если код ответа вне ожидаемых.
        """
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method, url, json=data, params=params, headers=self.headers, timeout=self.timeout
            )
        except requests.exceptions.RequestException as error:
            raise RuntimeError(f"Ошибка сети при запросе {method} {url}: {error}") from error

        if response.status_code not in expected_status:
            raise requests.HTTPError(
                f"{method} {path} -> {response.status_code}: {response.text[:500]}",
                response=response,
            )

        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    # ------------------------------------------------------------------
    # Проверка соединения
    # ------------------------------------------------------------------
    def test_connection(self) -> bool:
        """Запрашивает список рецептов, выводит результат и возвращает True/False."""
        try:
            data = self._make_request("GET", "/api/recipe/", expected_status=(200,))
            count = len(data.get("results", [])) if data else 0
            print(f"Соединение с API установлено. Рецептов в списке: {count}")
            return True
        except (requests.HTTPError, RuntimeError) as error:
            print(f"Ошибка соединения с API: {error}")
            return False

    # ------------------------------------------------------------------
    # Рецепты
    # ------------------------------------------------------------------
    def import_recipe_from_url(self, url: str) -> Dict[str, Any]:
        """
        Парсит рецепт по внешней ссылке (scraping).

        ВНИМАНИЕ: рецепт НЕ сохраняется в БД, а только парсится.
        Для сохранения получившийся словарь нужно передать в create_recipe().

        :return: распарсенный рецепт (поля name, steps и т.д.).
        """
        data = self._make_request("POST", "/api/recipe-from-source/", data={"url": url}, expected_status=(200, 201, 202))
        return data.get("recipe", data) if isinstance(data, dict) else data

    def create_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создаёт рецепт в БД.

        Минимальный payload: {"name": "..."}.
        Рецепт с ингредиентами:
            {"name": "...", "steps": [{"ingredients": [
                {"food": {"name": "Яблоко"}, "amount": 500, "unit": {"name": "г"}}]}]}

        :return: созданный рецепт (с id).
        """
        payload = dict(recipe_data)
        # API требует обязательное поле steps даже для пустого рецепта
        payload.setdefault("steps", [])
        return self._make_request("POST", "/api/recipe/", data=payload, expected_status=(201,))

    def import_and_create_recipe(self, url: str) -> Dict[str, Any]:
        """Удобный двухшаговый импорт: парсит ссылку, затем сохраняет рецепт в БД."""
        recipe = self.import_recipe_from_url(url)
        if not recipe or not recipe.get("name"):
            raise RuntimeError(f"Не удалось распарсить рецепт по ссылке: {url}")
        return self.create_recipe(recipe)

    def get_recipes(self, query: str = "") -> List[Dict[str, Any]]:
        """Возвращает список рецептов текущего пространства."""
        data = self._make_request("GET", "/api/recipe/", params={"query": query})
        return data.get("results", []) if data else []

    def get_recipe_ids(self) -> List[int]:
        """Возвращает id всех рецептов."""
        return [r["id"] for r in self.get_recipes()]

    def delete_recipe(self, recipe_id: int) -> None:
        """Удаляет рецепт по id."""
        self._make_request("DELETE", f"/api/recipe/{recipe_id}/", expected_status=(204,))

    def recipe_exists(self, recipe_id: int) -> bool:
        """Проверяет, существует ли рецепт с указанным id."""
        return any(r["id"] == recipe_id for r in self.get_recipes())

    # ------------------------------------------------------------------
    # Типы приёмов пищи (meal_type)
    # ------------------------------------------------------------------
    def create_meal_type(self, name: str) -> Dict[str, Any]:
        """Создаёт новый тип приёма пищи."""
        return self._make_request("POST", "/api/meal-type/", data={"name": name}, expected_status=(201,))

    def get_meal_types(self) -> List[Dict[str, Any]]:
        """Возвращает все типы приёма пищи."""
        data = self._make_request("GET", "/api/meal-type/", expected_status=(200,))
        return data.get("results", []) if data else []

    def get_meal_type_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Ищет тип приёма пищи по точному имени."""
        for meal_type in self.get_meal_types():
            if meal_type.get("name") == name:
                return meal_type
        return None

    # ------------------------------------------------------------------
    # План питания (meal plan)
    # ------------------------------------------------------------------
    def create_meal_plan(
        self,
        recipe: Dict[str, Any],
        meal_type: Dict[str, Any],
        from_date: datetime,
        to_date: datetime,
        servings: int = 1,
        title: Optional[str] = None,
        addshopping: bool = False,
    ) -> Dict[str, Any]:
        """
        Создаёт запись в плане питания.

        :param recipe: словарь рецепта с ключами id, name, keywords.
        :param meal_type: словарь типа пищи с ключами id, name.
        :param from_date: дата/время начала.
        :param to_date: дата/время окончания.
        :param servings: количество порций.
        :param title: произвольный заголовок (опционально).
        :param addshopping: добавлять ли ингредиенты рецепта в список покупок.
        :return: созданная запись плана.
        """
        payload: Dict[str, Any] = {
            "recipe": {
                "id": recipe["id"],
                "name": recipe.get("name", ""),
                "keywords": recipe.get("keywords", []),
            },
            "meal_type": {
                "id": meal_type["id"],
                "name": meal_type.get("name", ""),
            },
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "servings": servings,
            "shared": [],
        }
        if title:
            payload["title"] = title
        if addshopping:
            payload["addshopping"] = True

        # Сервер Tandoor нестабилен: POST /api/meal-plan/ эпизодически отвечает 500
        # даже при корректных данных. Повторяем запрос несколько раз (как для CSRF),
        # с растущей паузой, чтобы не усиливать нагрузку на сервер.
        # Повторное создание не засоряет данные: планы с QA_auto чистит фикстура cleanup_qa_auto.
        for attempt in range(MEAL_PLAN_CREATE_RETRIES):
            try:
                return self._make_request("POST", "/api/meal-plan/", data=payload, expected_status=(201,))
            except requests.HTTPError as error:
                is_server_error = error.response is not None and error.response.status_code >= 500
                if not is_server_error or attempt == MEAL_PLAN_CREATE_RETRIES - 1:
                    raise
                time.sleep(MEAL_PLAN_RETRY_DELAY_SECONDS * (attempt + 1))

    def get_meal_plan(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Возвращает записи плана питания.
        При передаче from_date/to_date (формат YYYY-MM-DD) фильтрует по диапазону.
        """
        params: Dict[str, Any] = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        data = self._make_request("GET", "/api/meal-plan/", params=params or None)
        return data.get("results", []) if data else []

    def get_meal_plan_by_id(self, meal_plan_id: int) -> Dict[str, Any]:
        """Возвращает запись плана питания по id."""
        return self._make_request("GET", f"/api/meal-plan/{meal_plan_id}/", expected_status=(200,))

    def delete_meal_plan(self, meal_plan_id: int) -> None:
        """Удаляет запись плана питания по id.

        Идемпотентно: если записи уже нет (404), считается удалённой.
        """
        try:
            self._make_request("DELETE", f"/api/meal-plan/{meal_plan_id}/", expected_status=(204,))
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                return
            raise

    def delete_all_meal_plans(self) -> int:
        """Удаляет все записи плана. Возвращает количество удалённых."""
        count = 0
        for meal_plan in self.get_meal_plan():
            self.delete_meal_plan(meal_plan["id"])
            count += 1
        return count

    # ------------------------------------------------------------------
    # Список покупок
    # ------------------------------------------------------------------
    def get_shopping_list(self) -> List[Dict[str, Any]]:
        """
        Возвращает позиции списка покупок из /api/shopping-list-entry/.
        (Готовые /api/shopping-list/ не создаются автоматически.)
        """
        data = self._make_request("GET", "/api/shopping-list-entry/", expected_status=(200,))
        return data.get("results", []) if data else []

    def delete_shopping_entry(self, entry_id: int) -> None:
        """Удаляет позицию из списка покупок."""
        self._make_request("DELETE", f"/api/shopping-list-entry/{entry_id}/", expected_status=(204,))

    def clear_shopping_list(self) -> int:
        """Удаляет все позиции списка покупок. Возвращает количество удалённых."""
        count = 0
        for entry in self.get_shopping_list():
            self.delete_shopping_entry(entry["id"])
            count += 1
        return count


def main() -> None:
    """Быстрый демо-прогон подключения к API."""
    client = TandoorAPIClient()

    if not client.test_connection():
        raise SystemExit("Нет соединения с API")

    meal_types = client.get_meal_types()
    meal_plan_count = len(client.get_meal_plan())
    shopping_count = len(client.get_shopping_list())

    print(f"[INFO] Типов приёма пищи: {len(meal_types)}")
    print(f"[INFO] Планов питания: {meal_plan_count}")
    print(f"[INFO] Позиций в списке покупок: {shopping_count}")


if __name__ == "__main__":
    main()
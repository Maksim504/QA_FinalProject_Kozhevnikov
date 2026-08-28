"""Генерация и подготовка тестовых данных (Задание №2).

- импорт рецептов по сохранённым ссылкам из data/recipes.json;
- получение их ID через API;
- создание запасного рецепта (fallback), если импорт не сработал;
- подготовка словаря данных для создания плана питания
  (рецепт, даты через datetime, тип питания, количество порций).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.client import TandoorAPIClient

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "recipes.json"
MARKER = "QA_auto"


def load_recipe_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Читает конфиг с рецептами из JSON-файла."""
    path = path or DATA_FILE
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def extract_recipes(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Возвращает список словарей рецептов из конфига."""
    return config.get("recipes", [])


def extract_fallback(config: Dict[str, Any]) -> Dict[str, Any]:
    """Возвращает запасной рецепт из конфига."""
    return config.get("fallback_recipe", {"name": "Салат из яблок", "steps": []})


def _to_recipe_ref(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """Приводит словарь рецепта к минимальному виду для плана питания."""
    return {
        "id": recipe_data["id"],
        "name": recipe_data.get("name", ""),
        "keywords": recipe_data.get("keywords", []),
    }


def import_recipes_from_links(
    api_client: TandoorAPIClient,
    config: Optional[Dict[str, Any]] = None,
    marker: str = MARKER,
) -> List[Dict[str, Any]]:
    """
    Импортирует рецепты по всем ссылкам из конфига и возвращает их ID.

    Сайты, которые сервис не умеет парсить (povarenok.ru), пропускаются.
    """
    config = config or load_recipe_config()
    created: List[Dict[str, Any]] = []

    for link in extract_recipes(config):
        if not link.get("importable", True):
            print(f"[SKIP] {link.get('name')} ({link.get('source')}) - импорт не поддерживается")
            continue
        try:
            parsed = api_client.import_recipe_from_url(link["url"])
            parsed["name"] = f"{marker} {parsed.get('name') or link.get('name')}"
            recipe = api_client.create_recipe(parsed)
            created.append(_to_recipe_ref(recipe))
            print(f"[OK] Импортирован рецепт id={recipe['id']}: {recipe['name']}")
        except Exception as error:
            print(f"[FAIL] {link.get('name')} ({link.get('source')}): {error}")

    return created


def create_fallback_recipe(
    api_client: TandoorAPIClient,
    config: Optional[Dict[str, Any]] = None,
    marker: str = MARKER,
) -> Dict[str, Any]:
    """
    Создаёт рецепт через API напрямую (с ингредиентами), если импорт не сработал.
    Нужен для тестов списка покупок.
    """
    config = config or load_recipe_config()
    fallback = extract_fallback(config)
    payload: Dict[str, Any] = {
        "name": f"{marker} {fallback.get('name', 'Салат из яблок')}",
        "steps": fallback.get("steps", []),
    }
    recipe = api_client.create_recipe(payload)
    print(f"[OK] Создан запасной рецепт id={recipe['id']}: {recipe['name']}")
    return _to_recipe_ref(recipe)


def get_or_create_recipe_for_tests(
    api_client: TandoorAPIClient,
    config: Optional[Dict[str, Any]] = None,
    marker: str = MARKER,
) -> Dict[str, Any]:
    """
    Возвращает валидный рецепт для тестов:
    1) если на сервере уже есть рецепты - возвращает первый (существующий);
    2) иначе пытается импортировать по ссылкам;
    3) если импорт не удался - создаёт запасной рецепт через API.
    """
    existing = api_client.get_recipes()
    if existing:
        return _to_recipe_ref(existing[0])

    created = import_recipes_from_links(api_client, config=config, marker=marker)
    if created:
        return created[0]

    return create_fallback_recipe(api_client, config=config, marker=marker)


def prepare_meal_plan_payload(
    recipe: Dict[str, Any],
    meal_type: Dict[str, Any],
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    servings: int = 1,
    title: Optional[str] = None,
    addshopping: bool = False,
) -> Dict[str, Any]:
    """
    Готовит словарь параметров для создания плана питания.

    Ключи совпадают с параметрами TandoorAPIClient.create_meal_plan,
    поэтому вызов выполняется через: api_client.create_meal_plan(**payload).
    """
    now = from_date or datetime.now()
    from_ts = (from_date or now).replace(hour=12, minute=0, second=0, microsecond=0)
    to_ts = (to_date or from_ts).replace(hour=12, minute=0, second=0, microsecond=0)

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
        "from_date": from_ts,
        "to_date": to_ts,
        "servings": servings,
    }
    if title:
        payload["title"] = title
    if addshopping:
        payload["addshopping"] = True
    return payload


def cleanup_qa_auto_plans(
    api_client: TandoorAPIClient,
    marker: str = MARKER,
    clear_shopping: bool = True,
) -> None:
    """
    Удаляет созданные тестами планы питания (заголовок начинается с marker)
    и, опционально, очищает лист покупок.
    """
    for plan in api_client.get_meal_plan():
        title = plan.get("title") or ""
        if title.startswith(marker):
            api_client.delete_meal_plan(plan["id"])
    if clear_shopping:
        api_client.clear_shopping_list()


def main() -> None:
    """Демо-прогон: импортирует рецепты из файла и выводит их ID."""
    client = TandoorAPIClient()
    if not client.test_connection():
        raise SystemExit("Нет соединения с API")

    config = load_recipe_config()
    recipes = import_recipes_from_links(client, config)

    if recipes:
        meal_type = client.get_meal_type_by_name("Завтрак") or client.get_meal_types()[0]
        payload = prepare_meal_plan_payload(recipes[0], meal_type, addshopping=False)
        print(f"\nПример данных для создания плана питания:")
        print(f"  рецепт  : id={payload['recipe']['id']} {payload['recipe']['name']}")
        print(f"  тип еды : id={payload['meal_type']['id']} {payload['meal_type']['name']}")
        print(f"  даты    : {payload['from_date']} -> {payload['to_date']}")
        print(f"  порции  : {payload['servings']}")
    else:
        print("Ни один рецепт не был импортирован.")


if __name__ == "__main__":
    main()
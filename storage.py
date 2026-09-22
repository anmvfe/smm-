"""Общее JSON-хранилище для сущностей, привязанных к клиенту (контент-план, сценарии,
посты, реклама). Каждый вид сущности ("kind") хранится в отдельном файле на клиента:
data/<kind>/<client_id>.json — со списком записей, у каждой есть свой "id".
"""

import datetime
import uuid
from pathlib import Path

from common import load_json, save_json

DATA_DIR = "data"


def _path(kind: str, client_id: str) -> str:
    return str(Path(DATA_DIR) / kind / f"{client_id}.json")


def load_items(kind: str, client_id: str) -> list[dict]:
    """Возвращает список сохранённых записей данного вида для клиента."""
    path = _path(kind, client_id)
    if not Path(path).exists():
        return []
    data = load_json(path)
    return data.get("items", [])


def save_items(kind: str, client_id: str, items: list[dict]) -> None:
    """Сохраняет список записей данного вида для клиента."""
    save_json({"items": items}, _path(kind, client_id))


def add_item(kind: str, client_id: str, fields: dict) -> dict:
    """Добавляет новую запись (с автоматическим id и датой создания) и сохраняет её."""
    items = load_items(kind, client_id)
    item = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        **fields,
    }
    items.append(item)
    save_items(kind, client_id, items)
    return item


def update_item(kind: str, client_id: str, item_id: str, **fields) -> dict | None:
    """Обновляет поля существующей записи. Возвращает обновлённую запись или None."""
    items = load_items(kind, client_id)
    for item in items:
        if item["id"] == item_id:
            item.update(fields)
            save_items(kind, client_id, items)
            return item
    return None


def delete_item(kind: str, client_id: str, item_id: str) -> bool:
    """Удаляет запись по id. Возвращает True, если запись была найдена и удалена."""
    items = load_items(kind, client_id)
    new_items = [i for i in items if i["id"] != item_id]
    if len(new_items) == len(items):
        return False
    save_items(kind, client_id, new_items)
    return True


def delete_all_for_client(client_id: str, kinds: list[str]) -> None:
    """Удаляет все файлы данных клиента для перечисленных видов сущностей (при удалении клиента)."""
    for kind in kinds:
        path = Path(_path(kind, client_id))
        if path.exists():
            path.unlink()

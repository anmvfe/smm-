"""Хранение и управление клиентами SaaS-приложения (простое JSON-хранилище на диске,
один файл на всех клиентов)."""

import uuid
from pathlib import Path

from common import load_json, save_json

CLIENTS_PATH = "data/clients.json"

# Виды сущностей, привязанных к клиенту — используются при каскадном удалении клиента.
CLIENT_DATA_KINDS = ["content_plans", "reels_scripts", "posts", "ads"]


def _ensure_storage(path: str = CLIENTS_PATH) -> None:
    """Создаёт файл хранилища клиентов, если он ещё не существует."""
    if not Path(path).exists():
        save_json({"clients": []}, path)


def list_clients(path: str = CLIENTS_PATH) -> list[dict]:
    """Возвращает список всех сохранённых клиентов."""
    _ensure_storage(path)
    data = load_json(path)
    return data.get("clients", [])


def get_client(client_id: str, path: str = CLIENTS_PATH) -> dict | None:
    """Возвращает клиента по id или None, если не найден."""
    for client in list_clients(path):
        if client["id"] == client_id:
            return client
    return None


def add_client(
    name: str,
    social_link: str,
    description: str,
    tone_of_voice: str,
    goals: str,
    path: str = CLIENTS_PATH,
) -> dict:
    """Добавляет нового клиента и сохраняет хранилище на диск. Возвращает добавленного клиента.

    social_link — ссылка на соцсеть клиента, сохраняется как есть, без автоматического
    разбора/парсинга — используется только для справки.
    description — краткое описание бизнеса и ниши.
    goals — произвольный текст: что клиент/пользователь хочет получить от контента.
    """
    _ensure_storage(path)
    data = load_json(path)

    client = {
        "id": str(uuid.uuid4()),
        "name": name,
        "social_link": social_link,
        "description": description,
        "tone_of_voice": tone_of_voice,
        "goals": goals,
    }

    data.setdefault("clients", []).append(client)
    save_json(data, path)
    return client


def update_client(client_id: str, path: str = CLIENTS_PATH, **fields) -> dict | None:
    """Обновляет поля существующего клиента. Возвращает обновлённого клиента или None."""
    _ensure_storage(path)
    data = load_json(path)

    for client in data.get("clients", []):
        if client["id"] == client_id:
            client.update(fields)
            save_json(data, path)
            return client
    return None


def delete_client(client_id: str, path: str = CLIENTS_PATH) -> bool:
    """Удаляет клиента по id вместе со всеми привязанными к нему данными
    (контент-планы, сценарии, посты, реклама). Возвращает True, если клиент был найден."""
    _ensure_storage(path)
    data = load_json(path)

    clients = data.get("clients", [])
    new_clients = [c for c in clients if c["id"] != client_id]
    if len(new_clients) == len(clients):
        return False

    data["clients"] = new_clients
    save_json(data, path)

    from storage import delete_all_for_client
    delete_all_for_client(client_id, CLIENT_DATA_KINDS)

    return True

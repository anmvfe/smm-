"""Текстовые сценарии рилсов (раскадровка по секундам) для клиента: генерация через
Claude API, ручное редактирование, хранение списка сценариев в JSON, привязанном к клиенту."""

import argparse

from clients import get_client
from common import DEFAULT_MODEL, get_client as get_anthropic_client
from storage import add_item, delete_item, load_items, update_item

KIND = "reels_scripts"

REELS_SCRIPT_PROMPT = """\
Ты — опытный сценарист коротких видео для соцсетей (Reels/TikTok/Shorts). Напиши текстовый \
сценарий рилса для следующего клиента:

- Имя/бренд: {name}
- Описание бизнеса и ниши: {description}
- Tone of voice: {tone_of_voice}
- Что клиент хочет получить от контента: {goals}

Идея / тема рилса: {idea}
Желаемая длительность: {duration} секунд

Разбей сценарий на сцены по секундам (раскадровка). Для каждой сцены укажи:
- тайминг (например "0-3 сек"),
- что происходит / что показывать в кадре,
- что говорить (текст закадрового голоса или реплики в кадре, если есть),
- текст на экране, если он нужен в этой сцене.

Сценарий должен быть выдержан в указанном tone of voice, с цепляющим началом в первые 2-3 \
секунды и чётким призывом к действию в конце.

Ответь готовым текстом на русском языке в виде списка сцен, без JSON, примерно в таком формате:

Сцена 1 (0-3 сек):
Кадр: <что происходит в кадре>
Голос/реплика: <что говорить>
Текст на экране: <текст или "нет">

Сцена 2 (...):
...
"""


def generate_reels_script_text(
    idea: str,
    client_id: str,
    duration: int = 30,
    model: str = DEFAULT_MODEL,
) -> str:
    """Генерирует текст сценария рилса (без сохранения)."""
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Клиент с id={client_id} не найден.")

    prompt = REELS_SCRIPT_PROMPT.format(
        name=client["name"],
        description=client["description"],
        tone_of_voice=client["tone_of_voice"],
        goals=client.get("goals", ""),
        idea=idea,
        duration=duration,
    )

    anthropic_client = get_anthropic_client()
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def generate_and_save_reels_script(client_id: str, idea: str, duration: int = 30) -> dict:
    """Генерирует сценарий рилса и сохраняет его в список сценариев клиента."""
    content = generate_reels_script_text(idea, client_id, duration)
    return add_item(KIND, client_id, {"idea": idea, "duration": duration, "content": content})


def list_reels_scripts(client_id: str) -> list[dict]:
    """Возвращает список сохранённых сценариев клиента (новые сверху)."""
    items = load_items(KIND, client_id)
    return sorted(items, key=lambda i: i.get("created_at", ""), reverse=True)


def update_reels_script(client_id: str, item_id: str, **fields) -> dict | None:
    """Обновляет сохранённый сценарий (например, после ручного редактирования текста)."""
    return update_item(KIND, client_id, item_id, **fields)


def delete_reels_script(client_id: str, item_id: str) -> bool:
    """Удаляет сохранённый сценарий."""
    return delete_item(KIND, client_id, item_id)


def main():
    parser = argparse.ArgumentParser(description="Генерация текстового сценария рилса для клиента")
    parser.add_argument("client_id", help="ID клиента (см. data/clients.json)")
    parser.add_argument("idea", help="Идея / тема рилса")
    parser.add_argument("--duration", type=int, default=30, help="Желаемая длительность в секундах")
    args = parser.parse_args()

    item = generate_and_save_reels_script(args.client_id, args.idea, args.duration)
    print(item["content"])


if __name__ == "__main__":
    main()

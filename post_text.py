"""Тексты постов (подпись, хэштеги, призыв к действию) под tone of voice клиента: генерация
через Claude API, ручное редактирование, хранение списка постов в JSON, привязанном к клиенту."""

import argparse

from clients import get_client
from common import DEFAULT_MODEL, get_client as get_anthropic_client
from storage import add_item, delete_item, load_items, update_item

KIND = "posts"

POST_TEXT_PROMPT = """\
Ты — опытный копирайтер для соцсетей. Напиши готовый текст поста для следующего клиента:

- Имя/бренд: {name}
- Описание бизнеса и ниши: {description}
- Tone of voice: {tone_of_voice}
- Что клиент хочет получить от контента: {goals}

Тема поста: {topic}
Формат поста: {format}

Напиши:
1. Подпись к посту (caption) — раскрывающую тему, выдержанную в указанном tone of voice, \
подходящую по длине под указанный формат.
2. Набор из 5-10 релевантных хэштегов.
3. Чёткий призыв к действию (call to action) в конце подписи.

Ответь готовым текстом на русском языке, без пояснений и без JSON — просто текст поста, \
который можно сразу скопировать и опубликовать. Структурируй ответ так:

Подпись:
<текст подписи с призывом к действию в конце>

Хэштеги:
<хэштеги через пробел>
"""


def generate_post_text_content(
    topic: str,
    post_format: str,
    client_id: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Генерирует текст поста (без сохранения)."""
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Клиент с id={client_id} не найден.")

    prompt = POST_TEXT_PROMPT.format(
        name=client["name"],
        description=client["description"],
        tone_of_voice=client["tone_of_voice"],
        goals=client.get("goals", ""),
        topic=topic,
        format=post_format,
    )

    anthropic_client = get_anthropic_client()
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def generate_and_save_post(client_id: str, topic: str, post_format: str) -> dict:
    """Генерирует текст поста и сохраняет его в список постов клиента."""
    content = generate_post_text_content(topic, post_format, client_id)
    return add_item(KIND, client_id, {"topic": topic, "format": post_format, "content": content})


def list_posts(client_id: str) -> list[dict]:
    """Возвращает список сохранённых постов клиента (новые сверху)."""
    items = load_items(KIND, client_id)
    return sorted(items, key=lambda i: i.get("created_at", ""), reverse=True)


def update_post_item(client_id: str, item_id: str, **fields) -> dict | None:
    """Обновляет сохранённый пост (например, после ручного редактирования текста)."""
    return update_item(KIND, client_id, item_id, **fields)


def delete_post_item(client_id: str, item_id: str) -> bool:
    """Удаляет сохранённый пост."""
    return delete_item(KIND, client_id, item_id)


def main():
    parser = argparse.ArgumentParser(description="Генерация текста поста для клиента")
    parser.add_argument("client_id", help="ID клиента (см. data/clients.json)")
    parser.add_argument("topic", help="Тема поста")
    parser.add_argument("--format", default="статичный пост", help="Формат поста")
    args = parser.parse_args()

    item = generate_and_save_post(args.client_id, args.topic, args.format)
    print(item["content"])


if __name__ == "__main__":
    main()

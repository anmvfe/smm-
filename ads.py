"""Рекламные тексты для платных кампаний клиента: генерация через Claude API (заголовок,
основной текст, несколько вариантов hook, призыв к действию), ручное редактирование,
хранение списка объявлений в JSON, привязанном к клиенту."""

import argparse

from clients import get_client
from common import DEFAULT_MODEL, extract_json, get_client as get_anthropic_client
from storage import add_item, delete_item, load_items, update_item

KIND = "ads"

AD_FORMAT_OPTIONS = ["Instagram/Facebook объявление", "Короткий текст для сторис-рекламы"]

AD_PROMPT = """\
Ты — опытный копирайтер рекламных кампаний в соцсетях. Составь рекламный текст для \
платной кампании следующего клиента:

- Имя/бренд: {name}
- Описание бизнеса и ниши: {description}
- Tone of voice: {tone_of_voice}
- Что клиент хочет получить от контента: {goals}

Тема / оффер рекламной кампании: {topic}
Формат объявления: {ad_format}

Составь:
1. Заголовок (headline) — короткий и цепляющий.
2. Основной текст объявления (body) — раскрывающий оффер, выдержанный в tone of voice, \
подходящий по длине под указанный формат (для сторис-рекламы — короче и динамичнее, чем для \
обычного объявления в ленте).
3. 3 разных варианта hook — первой фразы, которая должна зацепить внимание в первые секунды.
4. Чёткий призыв к действию (call to action).

Ответь СТРОГО в формате JSON без пояснений, по такой схеме:
{{
  "headline": "<заголовок>",
  "body": "<основной текст>",
  "hooks": ["<вариант hook 1>", "<вариант hook 2>", "<вариант hook 3>"],
  "cta": "<призыв к действию>"
}}
"""


def generate_ad_content(
    topic: str,
    ad_format: str,
    client_id: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Генерирует рекламный текст (без сохранения). Возвращает словарь с полями
    headline, body, hooks, cta."""
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Клиент с id={client_id} не найден.")

    prompt = AD_PROMPT.format(
        name=client["name"],
        description=client["description"],
        tone_of_voice=client["tone_of_voice"],
        goals=client.get("goals", ""),
        topic=topic,
        ad_format=ad_format,
    )

    anthropic_client = get_anthropic_client()
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = "".join(block.text for block in message.content if block.type == "text")
    return extract_json(response_text)


def generate_and_save_ad(client_id: str, topic: str, ad_format: str) -> dict:
    """Генерирует рекламный текст и сохраняет его в список объявлений клиента."""
    ad = generate_ad_content(topic, ad_format, client_id)
    return add_item(KIND, client_id, {
        "topic": topic,
        "format": ad_format,
        "headline": ad.get("headline", ""),
        "body": ad.get("body", ""),
        "hooks": ad.get("hooks", []),
        "cta": ad.get("cta", ""),
    })


def list_ads(client_id: str) -> list[dict]:
    """Возвращает список сохранённых рекламных текстов клиента (новые сверху)."""
    items = load_items(KIND, client_id)
    return sorted(items, key=lambda i: i.get("created_at", ""), reverse=True)


def update_ad(client_id: str, item_id: str, **fields) -> dict | None:
    """Обновляет сохранённый рекламный текст (например, после ручного редактирования)."""
    return update_item(KIND, client_id, item_id, **fields)


def delete_ad(client_id: str, item_id: str) -> bool:
    """Удаляет сохранённый рекламный текст."""
    return delete_item(KIND, client_id, item_id)


def main():
    parser = argparse.ArgumentParser(description="Генерация рекламного текста для клиента")
    parser.add_argument("client_id", help="ID клиента (см. data/clients.json)")
    parser.add_argument("topic", help="Тема / оффер рекламной кампании")
    parser.add_argument("--format", default=AD_FORMAT_OPTIONS[0], help="Формат объявления")
    args = parser.parse_args()

    item = generate_and_save_ad(args.client_id, args.topic, args.format)
    print(f"Заголовок: {item['headline']}\n\nТекст: {item['body']}\n\nHooks: {item['hooks']}\n\nCTA: {item['cta']}")


if __name__ == "__main__":
    main()

"""Контент-план клиента на 2 недели: генерация через Claude API, ручное редактирование,
построчная перегенерация, хранение в JSON, привязанном к клиенту."""

import argparse
import csv
import datetime

from clients import get_client
from common import DEFAULT_MODEL, extract_json, get_client as get_anthropic_client
from storage import add_item, delete_item, load_items, save_items, update_item

KIND = "content_plans"

CONTENT_PLAN_PROMPT = """\
Ты — опытный SMM-специалист. Составь контент-план на 2 недели (14 дней), начиная с \
{start_date}, для следующего клиента:

- Имя/бренд: {name}
- Описание бизнеса и ниши: {description}
- Tone of voice: {tone_of_voice}
- Что клиент хочет получить от контента: {goals}

Для каждого дня предложи ОДИН пост (не обязательно публиковать каждый день, но старайся \
дать разнообразный план на 14 дней с логичным чередованием форматов и тем). Для каждого поста укажи:
- дату публикации (в формате YYYY-MM-DD),
- тему поста (коротко и конкретно),
- формат: один из "сторис", "рилс", "карусель", "статичный пост",
- короткое обоснование, почему эта тема и формат подходят именно сейчас (1-2 предложения).

Учитывай нишу, tone of voice и цели клиента, чередуй форматы, избегай повторов одних и тех же тем.

Ответь СТРОГО в формате JSON без пояснений, по такой схеме:
{{
  "posts": [
    {{
      "date": "YYYY-MM-DD",
      "topic": "<тема поста>",
      "format": "сторис" | "рилс" | "карусель" | "статичный пост",
      "rationale": "<обоснование>"
    }}
  ]
}}
"""

SINGLE_POST_PROMPT = """\
Ты — опытный SMM-специалист. Предложи ОДНУ идею поста для следующего клиента:

- Имя/бренд: {name}
- Описание бизнеса и ниши: {description}
- Tone of voice: {tone_of_voice}
- Что клиент хочет получить от контента: {goals}

Дата публикации: {date}
{existing_context}

Ответь СТРОГО в формате JSON без пояснений, по такой схеме:
{{
  "date": "YYYY-MM-DD",
  "topic": "<тема поста>",
  "format": "сторис" | "рилс" | "карусель" | "статичный пост",
  "rationale": "<обоснование>"
}}
"""


def _call_claude_json(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 4096) -> dict:
    anthropic_client = get_anthropic_client()
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = "".join(block.text for block in message.content if block.type == "text")
    return extract_json(response_text)


def generate_content_plan(client_id: str, model: str = DEFAULT_MODEL, start_date: str | None = None) -> list[dict]:
    """Генерирует контент-план на 2 недели для клиента, сохраняет его (заменяя предыдущий)
    и возвращает список постов."""
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Клиент с id={client_id} не найден.")

    if start_date is None:
        start_date = datetime.date.today().isoformat()

    prompt = CONTENT_PLAN_PROMPT.format(
        start_date=start_date,
        name=client["name"],
        description=client["description"],
        tone_of_voice=client["tone_of_voice"],
        goals=client.get("goals", ""),
    )
    plan = _call_claude_json(prompt)
    posts = plan.get("posts", [])

    save_items(KIND, client_id, [])
    items = []
    for post in posts:
        item = add_item(KIND, client_id, {
            "date": post.get("date", ""),
            "topic": post.get("topic", ""),
            "format": post.get("format", ""),
            "rationale": post.get("rationale", ""),
        })
        items.append(item)
    return items


def regenerate_post(client_id: str, item_id: str, model: str = DEFAULT_MODEL) -> dict | None:
    """Перегенерирует одну строку контент-плана (сохраняя дату), возвращает обновлённую запись."""
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Клиент с id={client_id} не найден.")

    items = load_items(KIND, client_id)
    current = next((i for i in items if i["id"] == item_id), None)
    if not current:
        return None

    other_topics = [i["topic"] for i in items if i["id"] != item_id and i.get("topic")]
    existing_context = ""
    if other_topics:
        existing_context = "Другие темы, уже запланированные в этом контент-плане (не повторяй их): " + \
            "; ".join(other_topics)

    prompt = SINGLE_POST_PROMPT.format(
        name=client["name"],
        description=client["description"],
        tone_of_voice=client["tone_of_voice"],
        goals=client.get("goals", ""),
        date=current.get("date") or datetime.date.today().isoformat(),
        existing_context=existing_context,
    )
    post = _call_claude_json(prompt, max_tokens=1024)

    return update_item(
        KIND, client_id, item_id,
        date=post.get("date", current.get("date", "")),
        topic=post.get("topic", ""),
        format=post.get("format", ""),
        rationale=post.get("rationale", ""),
    )


def add_manual_post(client_id: str, date: str, topic: str, post_format: str, rationale: str = "") -> dict:
    """Добавляет строку контент-плана вручную (без обращения к Claude)."""
    return add_item(KIND, client_id, {
        "date": date, "topic": topic, "format": post_format, "rationale": rationale,
    })


def update_post(client_id: str, item_id: str, **fields) -> dict | None:
    """Обновляет поля строки контент-плана вручную."""
    return update_item(KIND, client_id, item_id, **fields)


def delete_post(client_id: str, item_id: str) -> bool:
    """Удаляет строку контент-плана."""
    return delete_item(KIND, client_id, item_id)


def list_content_plan(client_id: str) -> list[dict]:
    """Возвращает текущий контент-план клиента (отсортированный по дате)."""
    items = load_items(KIND, client_id)
    return sorted(items, key=lambda i: i.get("date", ""))


def content_plan_to_csv_rows(posts: list[dict]) -> list[list[str]]:
    """Преобразует список постов контент-плана в строки для CSV (с заголовком)."""
    rows = [["Дата", "Тема", "Формат", "Обоснование"]]
    for post in posts:
        rows.append([post.get("date", ""), post.get("topic", ""), post.get("format", ""), post.get("rationale", "")])
    return rows


def save_content_plan_csv(posts: list[dict], path: str) -> None:
    """Сохраняет контент-план в CSV-файл."""
    rows = content_plan_to_csv_rows(posts)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Генерация контент-плана на 2 недели для клиента")
    parser.add_argument("client_id", help="ID клиента (см. data/clients.json)")
    parser.add_argument("--csv", default=None, help="Дополнительно сохранить в CSV по этому пути")
    args = parser.parse_args()

    posts = generate_content_plan(args.client_id)
    if args.csv:
        save_content_plan_csv(posts, args.csv)

    print(f"Готово. Постов в плане: {len(posts)}.")


if __name__ == "__main__":
    main()

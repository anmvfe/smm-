"""Генерация контент-плана для клиента на 2 недели через Claude API."""

import argparse
import csv
import datetime
import json

from clients import get_client
from common import DEFAULT_MODEL, extract_json, get_client as get_anthropic_client, save_json

CONTENT_PLAN_PROMPT = """\
Ты — опытный SMM-специалист. Составь контент-план на 2 недели (14 дней), начиная с \
{start_date}, для следующего клиента:

- Имя/бренд: {name}
- Ниша: {niche}
- Описание бизнеса: {description}
- Tone of voice: {tone_of_voice}
- Соцсети: {social_links}

Для каждого дня предложи ОДИН пост (не обязательно публиковать каждый день, но старайся \
дать разнообразный план на 14 дней с логичным чередованием форматов и тем). Для каждого поста укажи:
- дату публикации (в формате YYYY-MM-DD),
- тему поста (коротко и конкретно),
- формат: один из "сторис", "рилс", "карусель", "статичный пост",
- короткое обоснование, почему эта тема и формат подходят именно сейчас (1-2 предложения).

Учитывай нишу и tone of voice клиента, чередуй форматы, избегай повторов одних и тех же тем.

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


def generate_content_plan(client_id: str, model: str = DEFAULT_MODEL, start_date: str | None = None) -> dict:
    """Генерирует контент-план на 2 недели для клиента с указанным id."""
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Клиент с id={client_id} не найден.")

    if start_date is None:
        start_date = datetime.date.today().isoformat()

    prompt = CONTENT_PLAN_PROMPT.format(
        start_date=start_date,
        name=client["name"],
        niche=client["niche"],
        description=client["description"],
        tone_of_voice=client["tone_of_voice"],
        social_links=client["social_links"],
    )

    anthropic_client = get_anthropic_client()
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = "".join(block.text for block in message.content if block.type == "text")
    plan = extract_json(response_text)
    return plan


def content_plan_to_csv_rows(plan: dict) -> list[list[str]]:
    """Преобразует контент-план в список строк для CSV (с заголовком)."""
    rows = [["Дата", "Тема", "Формат", "Обоснование"]]
    for post in plan.get("posts", []):
        rows.append([
            post.get("date", ""),
            post.get("topic", ""),
            post.get("format", ""),
            post.get("rationale", ""),
        ])
    return rows


def save_content_plan_csv(plan: dict, path: str) -> None:
    """Сохраняет контент-план в CSV-файл."""
    rows = content_plan_to_csv_rows(plan)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Генерация контент-плана на 2 недели для клиента")
    parser.add_argument("client_id", help="ID клиента (см. data/clients.json)")
    parser.add_argument("-o", "--output", default="content_plan.json", help="Куда сохранить результат (JSON)")
    parser.add_argument("--csv", default=None, help="Дополнительно сохранить в CSV по этому пути")
    args = parser.parse_args()

    plan = generate_content_plan(args.client_id)
    save_json(plan, args.output)
    if args.csv:
        save_content_plan_csv(plan, args.csv)

    print(f"Готово. Постов в плане: {len(plan.get('posts', []))}. Результат сохранён в {args.output}")


if __name__ == "__main__":
    main()

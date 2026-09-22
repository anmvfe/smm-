"""Генерация готового текста поста под tone of voice клиента через Claude API."""

import argparse

from clients import get_client
from common import DEFAULT_MODEL, get_client as get_anthropic_client

POST_TEXT_PROMPT = """\
Ты — опытный копирайтер для соцсетей. Напиши готовый текст поста для следующего клиента:

- Имя/бренд: {name}
- Ниша: {niche}
- Описание бизнеса: {description}
- Tone of voice: {tone_of_voice}

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


def generate_post_text(
    topic: str,
    post_format: str,
    client_id: str | None = None,
    tone_of_voice: str | None = None,
    name: str = "",
    niche: str = "",
    description: str = "",
    model: str = DEFAULT_MODEL,
) -> str:
    """Генерирует текст поста. Можно передать client_id (данные подтянутся автоматически)
    либо указать tone_of_voice и остальные поля вручную."""
    if client_id:
        client = get_client(client_id)
        if not client:
            raise ValueError(f"Клиент с id={client_id} не найден.")
        name = client["name"]
        niche = client["niche"]
        description = client["description"]
        tone_of_voice = client["tone_of_voice"]

    if not tone_of_voice:
        raise ValueError("Нужно указать либо client_id, либо tone_of_voice вручную.")

    prompt = POST_TEXT_PROMPT.format(
        name=name or "не указано",
        niche=niche or "не указана",
        description=description or "не указано",
        tone_of_voice=tone_of_voice,
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


def main():
    parser = argparse.ArgumentParser(description="Генерация текста поста под tone of voice клиента")
    parser.add_argument("topic", help="Тема поста")
    parser.add_argument("--format", default="статичный пост", help="Формат поста")
    parser.add_argument("--client-id", default=None, help="ID клиента (см. data/clients.json)")
    parser.add_argument("--tone", default=None, help="Tone of voice, если клиент не указан")
    args = parser.parse_args()

    text = generate_post_text(
        topic=args.topic,
        post_format=args.format,
        client_id=args.client_id,
        tone_of_voice=args.tone,
    )
    print(text)


if __name__ == "__main__":
    main()

"""Генерация текстового сценария рилса (раскадровка по секундам) через Claude API, без видео."""

import argparse

from clients import get_client
from common import DEFAULT_MODEL, get_client as get_anthropic_client

REELS_SCRIPT_PROMPT = """\
Ты — опытный сценарист коротких видео для соцсетей (Reels/TikTok/Shorts). Напиши текстовый \
сценарий рилса для следующего клиента:

- Имя/бренд: {name}
- Ниша: {niche}
- Tone of voice: {tone_of_voice}

Идея / описание рилса: {idea}
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


def generate_reels_script(
    idea: str,
    client_id: str | None = None,
    tone_of_voice: str | None = None,
    name: str = "",
    niche: str = "",
    duration: int = 30,
    model: str = DEFAULT_MODEL,
) -> str:
    """Генерирует текстовый сценарий рилса. Можно передать client_id либо tone_of_voice вручную."""
    if client_id:
        client = get_client(client_id)
        if not client:
            raise ValueError(f"Клиент с id={client_id} не найден.")
        name = client["name"]
        niche = client["niche"]
        tone_of_voice = client["tone_of_voice"]

    if not tone_of_voice:
        raise ValueError("Нужно указать либо client_id, либо tone_of_voice вручную.")

    prompt = REELS_SCRIPT_PROMPT.format(
        name=name or "не указано",
        niche=niche or "не указана",
        tone_of_voice=tone_of_voice,
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


def main():
    parser = argparse.ArgumentParser(description="Генерация текстового сценария рилса")
    parser.add_argument("idea", help="Идея / описание рилса")
    parser.add_argument("--duration", type=int, default=30, help="Желаемая длительность в секундах")
    parser.add_argument("--client-id", default=None, help="ID клиента (см. data/clients.json)")
    parser.add_argument("--tone", default=None, help="Tone of voice, если клиент не указан")
    args = parser.parse_args()

    script = generate_reels_script(
        idea=args.idea,
        client_id=args.client_id,
        tone_of_voice=args.tone,
        duration=args.duration,
    )
    print(script)


if __name__ == "__main__":
    main()

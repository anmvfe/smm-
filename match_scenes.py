"""Составление итогового монтажного плана (EDL) на основе анализа референса и клипов."""

import argparse
import json

from common import extract_json, get_client, load_json, save_json, DEFAULT_MODEL

MATCH_PROMPT = """\
Ты — эксперт по видеомонтажу. У тебя есть два JSON:

1. Анализ видео-референса (шаблона монтажа) со списком сцен, их таймингов, типов \
и текста на экране:
{reference_json}

2. Анализ моих сырых клипов с их описанием, наличием речи и лучшими отрезками внутри \
каждого клипа:
{clips_json}

Составь итоговый монтажный план (EDL — Edit Decision List): для каждой сцены референса \
подбери наиболее подходящий мой клип и конкретный отрезок внутри него.

Правила:
- Подбирай клипы по смыслу и типу содержимого (talking_head к talking_head, broll к broll и т.д.), \
но если точного совпадения нет — бери наиболее похожий по смыслу клип.
- Если клипов не хватает на все сцены референса — переиспользуй клипы повторно для похожих сцен \
или объединяй соседние короткие сцены референса в одну более длинную сцену в EDL (указав это в поле "merged_from").
- Длительность отрезка из клипа не должна превышать длительность сцены референса (end - start сцены); \
если это не критично, можно взять отрезок короче.
- Если исходный клип короче нужной сцены референса — используй клип целиком, НЕ растягивай его \
(не меняй скорость воспроизведения). В этом случае итоговая сцена в готовом видео будет короче, \
чем в референсе — это нормально.
- Переноси текст на экране (on_screen_text) и его положение (text_position) из сцены референса \
в соответствующую сцену EDL, если он там был.
- Сохраняй порядок сцен таким же, как в референсе.

Ответь СТРОГО в формате JSON без пояснений, по такой схеме:
{{
  "scenes": [
    {{
      "scene_index": 0,
      "reference_start": <число секунд>,
      "reference_end": <число секунд>,
      "merged_from": [<индексы сцен референса, если сцены были объединены>] | null,
      "source_clip": "<путь к исходному клипу, взятый из source_path в анализе клипов>",
      "clip_start": <число секунд, начало отрезка внутри клипа>,
      "clip_end": <число секунд, конец отрезка внутри клипа>,
      "on_screen_text": "<текст или null>",
      "text_position": "top" | "center" | "bottom" | null
    }}
  ]
}}
"""


def match_scenes(reference_path: str, clips_path: str, output_json: str, model: str = DEFAULT_MODEL) -> dict:
    """Строит EDL из анализа референса и клипов, сохраняет результат в JSON."""
    reference_data = load_json(reference_path)
    clips_data = load_json(clips_path)

    prompt = MATCH_PROMPT.format(
        reference_json=json.dumps(reference_data, ensure_ascii=False, indent=2),
        clips_json=json.dumps(clips_data, ensure_ascii=False, indent=2),
    )

    client = get_client()
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = "".join(block.text for block in message.content if block.type == "text")
    edl = extract_json(response_text)

    save_json(edl, output_json)
    return edl


def main():
    parser = argparse.ArgumentParser(description="Составление монтажного плана (EDL) из анализа референса и клипов")
    parser.add_argument("reference_json", help="Путь к JSON анализа референса")
    parser.add_argument("clips_json", help="Путь к JSON анализа клипов")
    parser.add_argument("-o", "--output", default="edl.json", help="Куда сохранить итоговый EDL")
    args = parser.parse_args()

    edl = match_scenes(args.reference_json, args.clips_json, args.output)
    print(f"Готово. Сцен в плане монтажа: {len(edl.get('scenes', []))}. Результат сохранён в {args.output}")


if __name__ == "__main__":
    main()

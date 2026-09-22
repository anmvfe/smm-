"""Анализ видео-референса: разбивка на сцены, тип каждой сцены, текст на экране, темп монтажа."""

import argparse
import shutil

from common import (
    ask_claude_with_frames,
    extract_frames,
    extract_json,
    get_video_duration,
    make_temp_dir,
    save_json,
)

REFERENCE_PROMPT = """\
Ты — эксперт по видеомонтажу. Тебе показаны кадры видео-референса (по одному кадру \
в секунду, по порядку). Общая длительность видео: {duration:.1f} секунд.

Проанализируй видео и определи:
1. Смену сцен — раздели видео на последовательные сцены с таймингами start/end (в секундах).
2. Тип каждой сцены: один из "talking_head" (говорящий человек в кадре), "broll" \
(вставки, б-ролл без говорящего), "text_screen" (экран с текстом/графикой как основной элемент), \
"other" (что-то другое).
3. Если на сцене есть текст на экране (заголовки, подписи, субтитры-акценты) — укажи \
сам текст и его примерное положение (одно из "top", "center", "bottom").
4. Общий темп монтажа всего видео: "fast" (частая смена планов, короткие сцены), \
"medium" или "slow".

Ответь СТРОГО в формате JSON без пояснений, по такой схеме:
{{
  "duration": <число секунд>,
  "pacing": "fast" | "medium" | "slow",
  "scenes": [
    {{
      "index": 0,
      "start": <число секунд>,
      "end": <число секунд>,
      "type": "talking_head" | "broll" | "text_screen" | "other",
      "on_screen_text": "<текст или null>",
      "text_position": "top" | "center" | "bottom" | null,
      "description": "<краткое описание сцены на русском>"
    }}
  ]
}}
"""


def analyze_reference(video_path: str, output_json: str, fps: float = 1.0) -> dict:
    """Анализирует видео-референс и сохраняет результат в JSON."""
    duration = get_video_duration(video_path)
    frames_dir = make_temp_dir("ref_frames_")
    try:
        frames = extract_frames(video_path, frames_dir, fps=fps)
        prompt = REFERENCE_PROMPT.format(duration=duration)
        response_text = ask_claude_with_frames(frames, prompt)
        data = extract_json(response_text)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)

    save_json(data, output_json)
    return data


def main():
    parser = argparse.ArgumentParser(description="Анализ видео-референса для монтажного плана")
    parser.add_argument("video", help="Путь к видео-референсу")
    parser.add_argument("-o", "--output", default="reference_analysis.json", help="Куда сохранить результат")
    parser.add_argument("--fps", type=float, default=1.0, help="Кадров в секунду для анализа")
    args = parser.parse_args()

    data = analyze_reference(args.video, args.output, fps=args.fps)
    print(f"Готово. Найдено сцен: {len(data.get('scenes', []))}. Результат сохранён в {args.output}")


if __name__ == "__main__":
    main()

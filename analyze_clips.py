"""Анализ сырых клипов пользователя: тип содержимого, описание, речь, лучшие отрезки."""

import argparse
import shutil
from pathlib import Path

from common import (
    ask_claude_with_frames,
    extract_frames,
    extract_json,
    get_video_duration,
    make_temp_dir,
    save_json,
)

CLIP_PROMPT = """\
Ты — эксперт по видеомонтажу. Тебе показаны кадры одного видеоклипа (по одному кадру \
в секунду, по порядку). Общая длительность клипа: {duration:.1f} секунд.

Проанализируй клип и определи:
1. Тип содержимого: например "talking_head", "broll", "text_screen", "other".
2. Короткое описание того, что происходит в клипе (на русском).
3. Есть ли в клипе речь (говорит ли кто-то в кадр) — true/false. Оценивай по видимым \
признакам (открытый рот, человек обращается к камере и т.п.), точную оценку речи по звуку \
ты сделать не можешь.
4. От 1 до 3 лучших отрезков внутри клипа для использования в монтаже — с таймингами \
start/end (в секундах) и коротким объяснением, почему этот отрезок хорош.

Ответь СТРОГО в формате JSON без пояснений, по такой схеме:
{{
  "duration": <число секунд>,
  "content_type": "talking_head" | "broll" | "text_screen" | "other",
  "description": "<краткое описание на русском>",
  "has_speech": true | false,
  "best_segments": [
    {{
      "start": <число секунд>,
      "end": <число секунд>,
      "reason": "<почему этот отрезок хорош>"
    }}
  ]
}}
"""


def analyze_clip(video_path: str, fps: float = 1.0) -> dict:
    """Анализирует один клип и возвращает словарь с результатом."""
    duration = get_video_duration(video_path)
    frames_dir = make_temp_dir("clip_frames_")
    try:
        frames = extract_frames(video_path, frames_dir, fps=fps)
        prompt = CLIP_PROMPT.format(duration=duration)
        response_text = ask_claude_with_frames(frames, prompt)
        data = extract_json(response_text)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)

    data["source_path"] = video_path
    return data


def analyze_clips(video_paths: list[str], output_json: str, fps: float = 1.0) -> dict:
    """Анализирует несколько клипов и сохраняет результат в JSON."""
    clips = []
    for path in video_paths:
        clip_data = analyze_clip(path, fps=fps)
        clip_data["clip_id"] = Path(path).stem
        clips.append(clip_data)

    result = {"clips": clips}
    save_json(result, output_json)
    return result


def main():
    parser = argparse.ArgumentParser(description="Анализ сырых клипов для монтажного плана")
    parser.add_argument("videos", nargs="+", help="Пути к видеоклипам")
    parser.add_argument("-o", "--output", default="clips_analysis.json", help="Куда сохранить результат")
    parser.add_argument("--fps", type=float, default=1.0, help="Кадров в секунду для анализа")
    args = parser.parse_args()

    data = analyze_clips(args.videos, args.output, fps=args.fps)
    print(f"Готово. Проанализировано клипов: {len(data['clips'])}. Результат сохранён в {args.output}")


if __name__ == "__main__":
    main()

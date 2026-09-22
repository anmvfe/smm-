"""Общие функции: нарезка видео на кадры, работа с Claude API, JSON-утилиты."""

import base64
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import anthropic

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


def get_api_key() -> str | None:
    """Ищет ключ Claude API: сначала в st.secrets (Streamlit Cloud), затем в переменных окружения."""
    try:
        import streamlit as st
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        # Streamlit не установлен, secrets.toml отсутствует, или вызов вне Streamlit — это нормально
        pass

    return os.environ.get("ANTHROPIC_API_KEY")


def get_client() -> anthropic.Anthropic:
    """Создаёт клиент Claude API, используя ключ из st.secrets или переменной окружения ANTHROPIC_API_KEY."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Не найден ключ ANTHROPIC_API_KEY. Локально: установите переменную окружения "
            "или создайте файл .env с этим ключом. На Streamlit Community Cloud: добавьте "
            "его в Settings → Secrets (см. README.md)."
        )
    return anthropic.Anthropic(api_key=api_key)


def extract_frames(video_path: str, output_dir: str, fps: float = 1.0) -> list[str]:
    """Нарезает видео на кадры через FFmpeg.

    video_path: путь к видеофайлу
    output_dir: папка, куда сохранять кадры (jpg)
    fps: сколько кадров в секунду извлекать (по умолчанию 1)

    Возвращает отсортированный список путей к кадрам.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_pattern = str(Path(output_dir) / "frame_%05d.jpg")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        output_pattern,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg не смог нарезать кадры из {video_path}.\n"
            f"Команда: {' '.join(cmd)}\nОшибка:\n{result.stderr}"
        )

    frames = sorted(Path(output_dir).glob("frame_*.jpg"))
    if not frames:
        raise RuntimeError(
            f"FFmpeg не создал ни одного кадра из {video_path}. "
            "Проверьте, что видеофайл не повреждён."
        )
    return [str(f) for f in frames]


def get_video_duration(video_path: str) -> float:
    """Возвращает длительность видео в секундах через ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe не смог определить длительность {video_path}:\n{result.stderr}")
    return float(result.stdout.strip())


def _encode_image(image_path: str) -> dict:
    """Кодирует изображение в base64 для отправки в Claude API."""
    ext = Path(image_path).suffix.lower()
    media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": data,
        },
    }


def ask_claude_with_frames(
    frames: list[str],
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
    max_frames: int = 40,
) -> str:
    """Отправляет кадры и текстовый промпт в Claude, возвращает текстовый ответ.

    Если кадров больше max_frames, они равномерно прореживаются, чтобы уложиться
    в разумный размер запроса.
    """
    if not frames:
        raise ValueError("Список кадров пуст, нечего отправлять в Claude API.")

    if len(frames) > max_frames:
        step = len(frames) / max_frames
        indices = [int(i * step) for i in range(max_frames)]
        frames = [frames[i] for i in indices]

    client = get_client()

    content = []
    for i, frame_path in enumerate(frames):
        content.append({"type": "text", "text": f"Кадр {i + 1}:"})
        content.append(_encode_image(frame_path))
    content.append({"type": "text", "text": prompt})

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}],
    )

    return "".join(block.text for block in message.content if block.type == "text")


def extract_json(text: str):
    """Извлекает JSON из текстового ответа модели.

    Claude иногда оборачивает JSON в пояснения или markdown-блоки ```json ... ```.
    Пытается найти и распарсить первый валидный JSON-объект или массив в тексте.
    """
    # Сначала пробуем найти markdown-блок с кодом
    code_block_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidates = []
    if code_block_match:
        candidates.append(code_block_match.group(1).strip())

    # Затем пробуем весь текст целиком
    candidates.append(text.strip())

    # И наконец — самый широкий фрагмент между первой { или [ и последней } или ]
    first_obj = text.find("{")
    first_arr = text.find("[")
    starts = [i for i in (first_obj, first_arr) if i != -1]
    if starts:
        start = min(starts)
        last_obj = text.rfind("}")
        last_arr = text.rfind("]")
        end = max(last_obj, last_arr)
        if end > start:
            candidates.append(text[start:end + 1].strip())

    for candidate in candidates:
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(
        "Не удалось извлечь корректный JSON из ответа Claude. "
        f"Ответ модели:\n{text[:2000]}"
    )


def save_json(data, path: str) -> None:
    """Сохраняет данные в JSON-файл с человекочитаемым форматированием."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: str):
    """Читает JSON-файл."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_temp_dir(prefix: str = "smm_") -> str:
    """Создаёт временную директорию и возвращает путь к ней."""
    return tempfile.mkdtemp(prefix=prefix)

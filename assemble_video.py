"""Сборка финального видео по EDL: обрезка отрезков, склейка, наложение текста, экспорт в .mp4."""

import argparse
import shutil
import subprocess
from pathlib import Path

from common import load_json, make_temp_dir

# Позиция текста в drawtext (x:y выражения ffmpeg)
TEXT_POSITIONS = {
    "top": "x=(w-text_w)/2:y=h*0.08",
    "center": "x=(w-text_w)/2:y=(h-text_h)/2",
    "bottom": "x=(w-text_w)/2:y=h*0.85",
}


def _escape_drawtext(text: str) -> str:
    """Экранирует спецсимволы для drawtext ffmpeg."""
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "’")
    text = text.replace("%", "\\%")
    return text


def _cut_segment(source: str, start: float, end: float, out_path: str, text: str | None, text_position: str | None) -> None:
    """Вырезает отрезок из клипа и опционально накладывает текст, сохраняет в out_path."""
    duration = max(0.01, end - start)
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", source, "-t", str(duration)]

    vf_filters = []
    if text:
        pos = TEXT_POSITIONS.get(text_position or "bottom", TEXT_POSITIONS["bottom"])
        escaped = _escape_drawtext(text)
        vf_filters.append(
            f"drawtext=text='{escaped}':fontcolor=white:fontsize=48:"
            f"box=1:boxcolor=black@0.5:boxborderw=10:{pos}"
        )

    if vf_filters:
        cmd += ["-vf", ",".join(vf_filters)]

    cmd += [
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast", "-crf", "20",
        "-avoid_negative_ts", "make_zero",
        out_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg не смог вырезать отрезок из {source}:\n{result.stderr}")


def assemble_video(edl_path: str, output_path: str) -> str:
    """Собирает финальное видео по EDL и сохраняет по output_path."""
    edl = load_json(edl_path)
    scenes = edl.get("scenes", [])
    if not scenes:
        raise ValueError("В EDL нет ни одной сцены — нечего собирать.")

    work_dir = make_temp_dir("assemble_")
    try:
        segment_paths = []
        for i, scene in enumerate(scenes):
            source = scene["source_clip"]
            start = float(scene["clip_start"])
            end = float(scene["clip_end"])
            text = scene.get("on_screen_text")
            text_position = scene.get("text_position")

            if not Path(source).exists():
                raise FileNotFoundError(f"Исходный клип не найден: {source} (сцена {i})")

            seg_path = str(Path(work_dir) / f"seg_{i:04d}.mp4")
            _cut_segment(source, start, end, seg_path, text, text_position)
            segment_paths.append(seg_path)

        concat_list_path = str(Path(work_dir) / "concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for seg_path in segment_paths:
                f.write(f"file '{seg_path}'\n")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast", "-crf", "20",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg не смог склеить финальное видео:\n{result.stderr}")

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Сборка финального видео по EDL")
    parser.add_argument("edl", help="Путь к JSON с монтажным планом (EDL)")
    parser.add_argument("-o", "--output", default="final_video.mp4", help="Путь для итогового видео")
    args = parser.parse_args()

    output_path = assemble_video(args.edl, args.output)
    print(f"Готово. Итоговое видео сохранено: {output_path}")


if __name__ == "__main__":
    main()

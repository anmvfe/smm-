"""Streamlit-интерфейс: загрузка референса и клипов, сборка видео по образцу монтажа."""

import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from analyze_clips import analyze_clips
from analyze_reference import analyze_reference
from assemble_video import assemble_video
from match_scenes import match_scenes

load_dotenv()

st.set_page_config(page_title="Монтаж по образцу", page_icon="🎬")
st.title("🎬 Сборка видео по образцу монтажа")
st.write(
    "Загрузите видео-референс (образец монтажа) и свои сырые клипы. "
    "Сервис проанализирует референс через Claude, подберёт под него ваши клипы "
    "и соберёт готовое видео."
)

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.warning(
        "Не найдена переменная окружения ANTHROPIC_API_KEY. "
        "Добавьте ключ Claude API в файл .env или в переменные окружения перед запуском "
        "(см. README.md)."
    )

reference_file = st.file_uploader("Видео-референс (образец монтажа)", type=["mp4", "mov", "m4v"])
clip_files = st.file_uploader(
    "Ваши сырые клипы (можно выбрать несколько)",
    type=["mp4", "mov", "m4v"],
    accept_multiple_files=True,
)

start_button = st.button("Собрать видео", type="primary", disabled=not (reference_file and clip_files))

if start_button:
    work_dir = tempfile.mkdtemp(prefix="smm_app_")

    try:
        ref_path = str(Path(work_dir) / reference_file.name)
        with open(ref_path, "wb") as f:
            f.write(reference_file.getbuffer())

        clip_paths = []
        for clip_file in clip_files:
            clip_path = str(Path(work_dir) / clip_file.name)
            with open(clip_path, "wb") as f:
                f.write(clip_file.getbuffer())
            clip_paths.append(clip_path)

        progress = st.progress(0, text="Начинаем...")
        status = st.empty()

        try:
            status.info("Шаг 1/4: анализируем референс...")
            reference_json_path = str(Path(work_dir) / "reference_analysis.json")
            reference_data = analyze_reference(ref_path, reference_json_path)
            progress.progress(25, text="Референс проанализирован")
            st.success(f"Референс проанализирован: найдено сцен — {len(reference_data.get('scenes', []))}")

            status.info("Шаг 2/4: анализируем ваши клипы...")
            clips_json_path = str(Path(work_dir) / "clips_analysis.json")
            clips_data = analyze_clips(clip_paths, clips_json_path)
            progress.progress(50, text="Клипы проанализированы")
            st.success(f"Проанализировано клипов: {len(clips_data.get('clips', []))}")

            status.info("Шаг 3/4: составляем монтажный план...")
            edl_path = str(Path(work_dir) / "edl.json")
            edl_data = match_scenes(reference_json_path, clips_json_path, edl_path)
            progress.progress(75, text="Монтажный план готов")
            st.success(f"Монтажный план составлен: сцен в плане — {len(edl_data.get('scenes', []))}")

            status.info("Шаг 4/4: собираем итоговое видео...")
            output_path = str(Path(work_dir) / "final_video.mp4")
            assemble_video(edl_path, output_path)
            progress.progress(100, text="Готово!")
            status.success("Видео успешно собрано!")

            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    "Скачать итоговое видео",
                    data=f.read(),
                    file_name="final_video.mp4",
                    mime="video/mp4",
                )

        except Exception as e:
            status.error(f"Произошла ошибка: {e}")
            st.exception(e)

    except Exception as e:
        st.error(f"Не удалось обработать загруженные файлы: {e}")

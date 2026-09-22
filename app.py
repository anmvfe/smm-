"""Streamlit-приложение: сборка видео по образцу монтажа + SMM-инструменты."""

import streamlit as st
from dotenv import load_dotenv

from common import get_api_key
from smm_tab import render_smm_tab
from video_tab import render_video_tab

load_dotenv()

st.set_page_config(page_title="SMM & Видео по образцу", page_icon="🎬", layout="wide")

if not get_api_key():
    st.warning(
        "Не найден ключ ANTHROPIC_API_KEY. Локально: добавьте его в файл .env или в "
        "переменные окружения. На Streamlit Community Cloud: добавьте его в "
        "Settings → Secrets (см. README.md)."
    )

tab_video, tab_smm = st.tabs(["🎬 Видео по образцу", "📋 SMM-инструменты"])

with tab_video:
    render_video_tab()

with tab_smm:
    render_smm_tab()

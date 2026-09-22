"""SaaS-приложение для SMM-специалиста: клиенты, контент-план, сценарии рилсов,
обработка видео, посты и реклама — на базе Claude API."""

import streamlit as st
from dotenv import load_dotenv

import clients as clients_module
from common import get_api_key
from ui_ads import render_ads_section
from ui_clients import render_clients_section
from ui_content_plan import render_content_plan_section
from ui_posts import render_posts_section
from ui_reels import render_reels_section
from video_tab import render_video_tab

load_dotenv()

st.set_page_config(page_title="SMM-помощник", page_icon="🧑‍💼", layout="wide")

if not get_api_key():
    st.warning(
        "Не найден ключ ANTHROPIC_API_KEY. Локально: добавьте его в файл .env или в "
        "переменные окружения. На Streamlit Community Cloud: добавьте его в "
        "Settings → Secrets (см. README.md)."
    )

SECTIONS_REQUIRING_CLIENT = {
    "Контент-план",
    "Сценарии для рилсов",
    "Посты и описания",
    "Реклама",
}

st.sidebar.title("🧑‍💼 SMM-помощник")

all_clients = clients_module.list_clients()
client_labels = [c["name"] for c in all_clients]

if "active_client_id" not in st.session_state:
    st.session_state["active_client_id"] = all_clients[0]["id"] if all_clients else None

st.sidebar.subheader("Активный клиент")
if all_clients:
    current_id = st.session_state.get("active_client_id")
    ids = [c["id"] for c in all_clients]
    current_index = ids.index(current_id) if current_id in ids else 0
    selected_label = st.sidebar.selectbox("Работаем с клиентом:", client_labels, index=current_index)
    st.session_state["active_client_id"] = all_clients[client_labels.index(selected_label)]["id"]
else:
    st.sidebar.info("Сначала добавьте клиента в разделе «Клиенты».")

st.sidebar.divider()

section = st.sidebar.radio(
    "Раздел",
    ["Клиенты", "Контент-план", "Сценарии для рилсов", "Обработка видео", "Посты и описания", "Реклама"],
)

active_client = None
if st.session_state.get("active_client_id"):
    active_client = clients_module.get_client(st.session_state["active_client_id"])

if section in SECTIONS_REQUIRING_CLIENT and not active_client:
    st.title(section)
    st.warning(
        "Сначала выберите или добавьте активного клиента. Перейдите в раздел «Клиенты» слева, "
        "добавьте клиента и выберите его в списке «Активный клиент» в сайдбаре."
    )
elif section == "Клиенты":
    render_clients_section()
elif section == "Контент-план":
    render_content_plan_section(active_client)
elif section == "Сценарии для рилсов":
    render_reels_section(active_client)
elif section == "Обработка видео":
    render_video_tab()
elif section == "Посты и описания":
    render_posts_section(active_client)
elif section == "Реклама":
    render_ads_section(active_client)

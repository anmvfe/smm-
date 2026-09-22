"""Раздел «Сценарии для рилсов»: генерация, список сохранённых сценариев,
ручное редактирование и удаление."""

import streamlit as st

from content_plan import list_content_plan
from reels_script import delete_reels_script, generate_and_save_reels_script, list_reels_scripts, update_reels_script


def _render_generate_form(client: dict) -> None:
    client_id = client["id"]
    st.subheader("Сгенерировать новый сценарий")

    plan_posts = list_content_plan(client_id)
    topic_options = ["Ввести тему вручную"] + [f"{p['date']}: {p['topic']}" for p in plan_posts]
    topic_choice = st.selectbox("Тема рилса", topic_options, key="reels_topic_select")

    if topic_choice == "Ввести тему вручную":
        idea = st.text_area(
            "Опишите идею рилса",
            placeholder="Например: 'до/после результата услуги', 'разбор частого вопроса "
                        "клиентов', 'закулисье процесса производства'",
            key="reels_idea_manual",
        )
    else:
        idea = topic_choice.split(": ", 1)[1]
        st.caption(f"Тема из контент-плана: {idea}")

    duration = st.slider("Желаемая длительность (секунд)", min_value=10, max_value=90, value=30, key="reels_duration_slider")

    if st.button("Сгенерировать сценарий", type="primary", key="generate_reels_script_button"):
        if not idea:
            st.error("Опишите идею рилса.")
        else:
            with st.spinner("Claude пишет сценарий..."):
                try:
                    generate_and_save_reels_script(client_id, idea, duration)
                    st.success("Сценарий сгенерирован и сохранён ниже.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Не удалось сгенерировать сценарий: {e}")


def _render_saved_scripts(client_id: str) -> None:
    st.subheader("Сохранённые сценарии")
    scripts = list_reels_scripts(client_id)
    if not scripts:
        st.info("Пока нет сохранённых сценариев — сгенерируйте первый выше.")
        return

    for script in scripts:
        item_id = script["id"]
        edit_key = f"editing_reel_{item_id}"
        is_editing = st.session_state.get(edit_key, False)

        title = f"{script.get('idea', 'Без темы')} ({script.get('duration', '?')} сек)"
        with st.expander(title):
            content = st.text_area(
                "Текст сценария", value=script.get("content", ""), height=300, key=f"reel_content_{item_id}"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Сохранить изменения", key=f"reel_save_{item_id}"):
                    update_reels_script(client_id, item_id, content=content)
                    st.success("Изменения сохранены.")
                    st.rerun()
            with col2:
                if st.button("Удалить сценарий", key=f"reel_delete_{item_id}"):
                    delete_reels_script(client_id, item_id)
                    st.rerun()


def render_reels_section(client: dict) -> None:
    st.header("🎥 Сценарии для рилсов")
    st.write(
        "Этот раздел создаёт только текстовый сценарий (раскадровку) — видео при этом не "
        "загружается и не монтируется. Для сборки видео используйте раздел «Обработка видео»."
    )

    _render_generate_form(client)
    st.divider()
    _render_saved_scripts(client["id"])

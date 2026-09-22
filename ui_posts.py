"""Раздел «Посты и описания»: генерация текста поста, список сохранённых постов,
ручное редактирование и удаление."""

import streamlit as st

from content_plan import list_content_plan
from post_text import delete_post_item, generate_and_save_post, list_posts, update_post_item

FORMAT_OPTIONS = ["сторис", "рилс", "карусель", "статичный пост"]


def _render_generate_form(client: dict) -> None:
    client_id = client["id"]
    st.subheader("Сгенерировать новый пост")

    plan_posts = list_content_plan(client_id)
    topic_options = ["Ввести тему вручную"] + [f"{p['date']}: {p['topic']}" for p in plan_posts]
    topic_choice = st.selectbox("Тема поста", topic_options, key="post_topic_select")

    if topic_choice == "Ввести тему вручную":
        topic = st.text_input("Введите тему поста", key="post_topic_manual")
        default_format = FORMAT_OPTIONS[0]
    else:
        topic = topic_choice.split(": ", 1)[1]
        matching = next((p for p in plan_posts if f"{p['date']}: {p['topic']}" == topic_choice), None)
        default_format = matching["format"] if matching and matching.get("format") in FORMAT_OPTIONS else FORMAT_OPTIONS[0]

    post_format = st.selectbox(
        "Формат поста", FORMAT_OPTIONS, index=FORMAT_OPTIONS.index(default_format), key="post_format_select"
    )

    if st.button("Сгенерировать текст поста", type="primary", key="generate_post_text_button"):
        if not topic:
            st.error("Укажите тему поста.")
        else:
            with st.spinner("Claude пишет текст поста..."):
                try:
                    generate_and_save_post(client_id, topic, post_format)
                    st.success("Пост сгенерирован и сохранён ниже.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Не удалось сгенерировать текст поста: {e}")


def _render_saved_posts(client_id: str) -> None:
    st.subheader("Сохранённые посты")
    posts = list_posts(client_id)
    if not posts:
        st.info("Пока нет сохранённых постов — сгенерируйте первый выше.")
        return

    for post in posts:
        item_id = post["id"]
        title = f"{post.get('topic', 'Без темы')} — {post.get('format', '')}"
        with st.expander(title):
            content = st.text_area(
                "Текст поста", value=post.get("content", ""), height=250, key=f"post_content_{item_id}"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Сохранить изменения", key=f"post_save_{item_id}"):
                    update_post_item(client_id, item_id, content=content)
                    st.success("Изменения сохранены.")
                    st.rerun()
            with col2:
                if st.button("Удалить пост", key=f"post_delete_{item_id}"):
                    delete_post_item(client_id, item_id)
                    st.rerun()


def render_posts_section(client: dict) -> None:
    st.header("✍️ Посты и описания")
    st.write("Генерация подписи, хэштегов и призыва к действию под tone of voice клиента.")

    _render_generate_form(client)
    st.divider()
    _render_saved_posts(client["id"])

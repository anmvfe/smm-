"""Раздел «Контент-план»: генерация на 2 недели, ручное редактирование, построчная
перегенерация, добавление/удаление строк, экспорт в CSV."""

import streamlit as st

from content_plan import (
    add_manual_post,
    content_plan_to_csv_rows,
    delete_post,
    generate_content_plan,
    list_content_plan,
    regenerate_post,
    update_post,
)

FORMAT_OPTIONS = ["сторис", "рилс", "карусель", "статичный пост"]


def _render_row(client_id: str, post: dict) -> None:
    item_id = post["id"]
    cols = st.columns([1.2, 2.2, 1.2, 2.6, 1, 1])

    new_date = cols[0].text_input("Дата", value=post.get("date", ""), key=f"cp_date_{item_id}", label_visibility="collapsed")
    new_topic = cols[1].text_input("Тема", value=post.get("topic", ""), key=f"cp_topic_{item_id}", label_visibility="collapsed")

    current_format = post.get("format", FORMAT_OPTIONS[0])
    format_index = FORMAT_OPTIONS.index(current_format) if current_format in FORMAT_OPTIONS else 0
    new_format = cols[2].selectbox(
        "Формат", FORMAT_OPTIONS, index=format_index, key=f"cp_format_{item_id}", label_visibility="collapsed"
    )

    new_rationale = cols[3].text_input(
        "Обоснование", value=post.get("rationale", ""), key=f"cp_rationale_{item_id}", label_visibility="collapsed"
    )

    if cols[4].button("💾", key=f"cp_save_{item_id}", help="Сохранить изменения в этой строке"):
        update_post(client_id, item_id, date=new_date, topic=new_topic, format=new_format, rationale=new_rationale)
        st.success("Строка сохранена.")
        st.rerun()

    if cols[5].button("🔄", key=f"cp_regen_{item_id}", help="Перегенерировать эту строку через Claude"):
        with st.spinner("Claude придумывает новую идею для этой даты..."):
            try:
                regenerate_post(client_id, item_id)
                st.rerun()
            except Exception as e:
                st.error(f"Не удалось перегенерировать строку: {e}")

    if st.button("🗑️ Удалить строку", key=f"cp_delete_{item_id}"):
        delete_post(client_id, item_id)
        st.rerun()

    st.divider()


def render_content_plan_section(client: dict) -> None:
    st.header("🗓️ Контент-план на 2 недели")
    client_id = client["id"]

    if st.button("Сгенерировать новый контент-план", type="primary", key="generate_content_plan_button"):
        with st.spinner("Claude составляет контент-план на 2 недели..."):
            try:
                posts = generate_content_plan(client_id)
                st.success(f"Готово! Постов в плане: {len(posts)}")
                st.rerun()
            except Exception as e:
                st.error(f"Не удалось составить контент-план: {e}")

    st.caption(
        "Генерация нового плана заменяет текущий. Отдельные строки ниже можно "
        "редактировать вручную, перегенерировать по одной или добавлять/удалять."
    )

    posts = list_content_plan(client_id)

    with st.expander("➕ Добавить строку вручную"):
        with st.form("add_manual_post_form", clear_on_submit=True):
            date = st.text_input("Дата (YYYY-MM-DD)")
            topic = st.text_input("Тема поста")
            post_format = st.selectbox("Формат", FORMAT_OPTIONS)
            rationale = st.text_input("Обоснование (необязательно)")
            if st.form_submit_button("Добавить"):
                if not date or not topic:
                    st.error("Укажите хотя бы дату и тему.")
                else:
                    add_manual_post(client_id, date, topic, post_format, rationale)
                    st.rerun()

    if not posts:
        st.info("Контент-план пока пуст. Сгенерируйте его кнопкой выше или добавьте строку вручную.")
        return

    header_cols = st.columns([1.2, 2.2, 1.2, 2.6, 1, 1])
    for col, label in zip(header_cols, ["Дата", "Тема", "Формат", "Обоснование", "", ""]):
        col.markdown(f"**{label}**")

    for post in posts:
        _render_row(client_id, post)

    rows = content_plan_to_csv_rows(posts)
    csv_text = "\n".join(",".join(f'"{cell}"' for cell in row) for row in rows)
    st.download_button(
        "Скачать контент-план как CSV",
        data=csv_text.encode("utf-8-sig"),
        file_name=f"content_plan_{client['name']}.csv",
        mime="text/csv",
    )

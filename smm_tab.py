"""Вкладка Streamlit-приложения: SaaS-инструменты для SMM-специалистов."""

import streamlit as st

import clients as clients_module
from content_plan import content_plan_to_csv_rows, generate_content_plan
from post_text import generate_post_text
from reels_script import generate_reels_script

TONE_OPTIONS = ["дружелюбный", "экспертный", "дерзкий", "другое (указать вручную)"]
FORMAT_OPTIONS = ["сторис", "рилс", "карусель", "статичный пост"]


def _client_options() -> tuple[list[str], dict[str, str]]:
    """Возвращает список подписей клиентов для selectbox и словарь подпись → id."""
    all_clients = clients_module.list_clients()
    labels = [f"{c['name']} ({c['niche']})" for c in all_clients]
    label_to_id = {f"{c['name']} ({c['niche']})": c["id"] for c in all_clients}
    return labels, label_to_id


def _render_clients_section() -> None:
    st.header("👤 Клиенты")
    st.write("Добавьте клиентов, чтобы дальше использовать их данные при генерации контента.")

    with st.form("add_client_form", clear_on_submit=True):
        st.subheader("Добавить нового клиента")
        name = st.text_input("Имя / бренд*")
        niche = st.text_input("Ниша*", placeholder="например: доставка еды, бьюти-салон, IT-курсы")
        description = st.text_area("Описание бизнеса*", placeholder="Чем занимается бренд, кто аудитория")
        tone_choice = st.selectbox("Tone of voice*", TONE_OPTIONS)
        tone_custom = ""
        if tone_choice == "другое (указать вручную)":
            tone_custom = st.text_input("Укажите свой tone of voice")
        social_links = st.text_area("Ссылки на соцсети", placeholder="Instagram, TikTok, VK и т.д., по одной строке")

        submitted = st.form_submit_button("Добавить клиента", type="primary")
        if submitted:
            tone_of_voice = tone_custom.strip() if tone_choice == "другое (указать вручную)" else tone_choice
            if not name or not niche or not description or not tone_of_voice:
                st.error("Заполните все обязательные поля (отмечены *).")
            else:
                clients_module.add_client(
                    name=name.strip(),
                    niche=niche.strip(),
                    description=description.strip(),
                    tone_of_voice=tone_of_voice,
                    social_links=social_links.strip(),
                )
                st.success(f"Клиент «{name}» добавлен.")
                st.rerun()

    st.subheader("Список клиентов")
    all_clients = clients_module.list_clients()
    if not all_clients:
        st.info("Пока нет ни одного клиента — добавьте первого через форму выше.")
        return

    for client in all_clients:
        with st.expander(f"{client['name']} — {client['niche']}"):
            st.write(f"**Tone of voice:** {client['tone_of_voice']}")
            st.write(f"**Описание:** {client['description']}")
            if client.get("social_links"):
                st.write(f"**Соцсети:** {client['social_links']}")
            if st.button("Удалить клиента", key=f"delete_client_{client['id']}"):
                clients_module.delete_client(client["id"])
                st.rerun()


def _render_content_plan_section() -> None:
    st.header("🗓️ Контент-план на 2 недели")

    labels, label_to_id = _client_options()
    if not labels:
        st.info("Сначала добавьте хотя бы одного клиента на вкладке «Клиенты».")
        return

    selected_label = st.selectbox("Выберите клиента", labels, key="content_plan_client_select")
    client_id = label_to_id[selected_label]

    if st.button("Сгенерировать контент-план", type="primary", key="generate_content_plan_button"):
        with st.spinner("Claude составляет контент-план на 2 недели..."):
            try:
                plan = generate_content_plan(client_id)
                st.session_state["content_plan_result"] = plan
                st.success(f"Готово! Постов в плане: {len(plan.get('posts', []))}")
            except Exception as e:
                st.error(f"Не удалось составить контент-план: {e}")

    plan = st.session_state.get("content_plan_result")
    if plan:
        rows = content_plan_to_csv_rows(plan)
        header, data_rows = rows[0], rows[1:]
        if data_rows:
            st.table([dict(zip(header, row)) for row in data_rows])

        csv_text = "\n".join(",".join(f'"{cell}"' for cell in row) for row in rows)
        st.download_button(
            "Скачать контент-план как CSV",
            data=csv_text.encode("utf-8-sig"),
            file_name="content_plan.csv",
            mime="text/csv",
        )


def _render_post_text_section() -> None:
    st.header("✍️ Текст поста")

    labels, label_to_id = _client_options()
    if not labels:
        st.info("Сначала добавьте хотя бы одного клиента на вкладке «Клиенты».")
        return

    selected_label = st.selectbox("Выберите клиента", labels, key="post_text_client_select")
    client_id = label_to_id[selected_label]

    plan = st.session_state.get("content_plan_result")
    topic_options = ["Ввести тему вручную"]
    if plan:
        topic_options += [f"{p['date']}: {p['topic']}" for p in plan.get("posts", [])]

    topic_choice = st.selectbox("Тема поста", topic_options, key="post_text_topic_select")
    if topic_choice == "Ввести тему вручную":
        topic = st.text_input("Введите тему поста", key="post_text_manual_topic")
    else:
        topic = topic_choice.split(": ", 1)[1]

    post_format = st.selectbox("Формат поста", FORMAT_OPTIONS, key="post_text_format_select")

    if st.button("Сгенерировать текст поста", type="primary", key="generate_post_text_button"):
        if not topic:
            st.error("Укажите тему поста.")
        else:
            with st.spinner("Claude пишет текст поста..."):
                try:
                    text = generate_post_text(topic=topic, post_format=post_format, client_id=client_id)
                    st.session_state["post_text_result"] = text
                except Exception as e:
                    st.error(f"Не удалось сгенерировать текст поста: {e}")

    if st.session_state.get("post_text_result"):
        st.text_area("Готовый текст поста", st.session_state["post_text_result"], height=300)


def _render_reels_script_section() -> None:
    st.header("🎥 Сценарий для рилса (текстовый)")

    labels, label_to_id = _client_options()
    client_id = None
    if labels:
        selected_label = st.selectbox(
            "Клиент (необязательно)", ["Без клиента"] + labels, key="reels_client_select"
        )
        if selected_label != "Без клиента":
            client_id = label_to_id[selected_label]

    tone_of_voice = None
    if not client_id:
        tone_of_voice = st.text_input(
            "Tone of voice (если клиент не выбран)", placeholder="например: дружелюбный", key="reels_manual_tone"
        )

    idea = st.text_area(
        "Идея / описание рилса",
        placeholder="Опишите словами, о чём рилс: например, 'до/после результата услуги', "
        "'разбор частого вопроса клиентов', 'закулисье процесса производства' и т.д.",
        key="reels_idea_input",
    )
    duration = st.slider("Желаемая длительность (секунд)", min_value=10, max_value=90, value=30, key="reels_duration_slider")

    if st.button("Сгенерировать сценарий", type="primary", key="generate_reels_script_button"):
        if not idea:
            st.error("Опишите идею рилса.")
        elif not client_id and not tone_of_voice:
            st.error("Выберите клиента или укажите tone of voice вручную.")
        else:
            with st.spinner("Claude пишет сценарий..."):
                try:
                    script = generate_reels_script(
                        idea=idea,
                        client_id=client_id,
                        tone_of_voice=tone_of_voice,
                        duration=duration,
                    )
                    st.session_state["reels_script_result"] = script
                except Exception as e:
                    st.error(f"Не удалось сгенерировать сценарий: {e}")

    if st.session_state.get("reels_script_result"):
        st.text_area("Готовый сценарий", st.session_state["reels_script_result"], height=400)


def render_smm_tab() -> None:
    """Отрисовывает вкладку SMM-инструментов с внутренней навигацией по разделам."""
    st.title("📋 SMM-инструменты")
    st.write("Ведение клиентов, контент-планы, тексты постов и сценарии рилсов на базе Claude API.")

    section = st.radio(
        "Раздел",
        ["Клиенты", "Контент-план", "Тексты постов", "Сценарии рилсов"],
        horizontal=True,
        key="smm_section_radio",
    )

    st.divider()

    if section == "Клиенты":
        _render_clients_section()
    elif section == "Контент-план":
        _render_content_plan_section()
    elif section == "Тексты постов":
        _render_post_text_section()
    elif section == "Сценарии рилсов":
        _render_reels_script_section()

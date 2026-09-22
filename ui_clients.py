"""Раздел «Клиенты»: список, добавление, редактирование и удаление клиентов."""

import streamlit as st

import clients as clients_module

TONE_OPTIONS = ["дружелюбный", "экспертный", "дерзкий", "другое (указать вручную)"]


def _tone_widget(key_prefix: str, current_value: str = "") -> str:
    """Отрисовывает выбор tone of voice (селект + поле для своего варианта). Возвращает значение."""
    options = TONE_OPTIONS
    if current_value in options[:-1]:
        default_index = options.index(current_value)
    elif current_value:
        default_index = len(options) - 1
    else:
        default_index = 0
    choice = st.selectbox("Tone of voice*", options, index=default_index, key=f"{key_prefix}_tone_select")
    if choice == "другое (указать вручную)":
        default_custom = current_value if current_value not in options[:-1] else ""
        return st.text_input("Укажите свой tone of voice", value=default_custom, key=f"{key_prefix}_tone_custom").strip()
    return choice


def _render_add_form() -> None:
    with st.form("add_client_form", clear_on_submit=True):
        st.subheader("Добавить нового клиента")
        name = st.text_input("Имя / бренд*")
        social_link = st.text_input(
            "Ссылка на соцсеть",
            placeholder="https://instagram.com/...",
            help="Ссылка сохраняется только для справки — приложение не переходит по ней "
                 "и не анализирует профиль автоматически.",
        )
        description = st.text_area(
            "Краткое описание бизнеса и ниши*",
            placeholder="Чем занимается бренд, кто аудитория, в какой нише работает",
        )
        tone_of_voice = _tone_widget("add_client")
        goals = st.text_area(
            "Что хочу получить (цели по контенту)*",
            placeholder="Например: больше узнаваемости бренда, рост подписчиков, продажи "
                        "через сторис, привлечение клиентов на консультацию",
        )

        submitted = st.form_submit_button("Добавить клиента", type="primary")
        if submitted:
            if not name or not description or not tone_of_voice or not goals:
                st.error("Заполните все обязательные поля (отмечены *).")
            else:
                clients_module.add_client(
                    name=name.strip(),
                    social_link=social_link.strip(),
                    description=description.strip(),
                    tone_of_voice=tone_of_voice,
                    goals=goals.strip(),
                )
                st.success(f"Клиент «{name}» добавлен.")
                st.rerun()


def _render_client_card(client: dict) -> None:
    edit_key = f"editing_client_{client['id']}"
    is_editing = st.session_state.get(edit_key, False)

    with st.expander(f"{client['name']}", expanded=is_editing):
        if not is_editing:
            st.write(f"**Tone of voice:** {client['tone_of_voice']}")
            st.write(f"**Описание и ниша:** {client['description']}")
            st.write(f"**Цели по контенту:** {client.get('goals', '')}")
            if client.get("social_link"):
                st.write(f"**Ссылка на соцсеть (справочно):** {client['social_link']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Редактировать", key=f"edit_btn_{client['id']}"):
                    st.session_state[edit_key] = True
                    st.rerun()
            with col2:
                if st.button("Удалить клиента", key=f"delete_btn_{client['id']}"):
                    clients_module.delete_client(client["id"])
                    if st.session_state.get("active_client_id") == client["id"]:
                        st.session_state["active_client_id"] = None
                    st.rerun()
        else:
            new_name = st.text_input("Имя / бренд*", value=client["name"], key=f"edit_name_{client['id']}")
            new_social_link = st.text_input(
                "Ссылка на соцсеть",
                value=client.get("social_link", ""),
                help="Ссылка сохраняется только для справки — приложение не переходит по ней "
                     "и не анализирует профиль автоматически.",
                key=f"edit_social_{client['id']}",
            )
            new_description = st.text_area(
                "Краткое описание бизнеса и ниши*", value=client["description"], key=f"edit_desc_{client['id']}"
            )
            new_tone = _tone_widget(f"edit_{client['id']}", client.get("tone_of_voice", ""))
            new_goals = st.text_area(
                "Что хочу получить (цели по контенту)*", value=client.get("goals", ""), key=f"edit_goals_{client['id']}"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Сохранить изменения", type="primary", key=f"save_btn_{client['id']}"):
                    if not new_name or not new_description or not new_tone or not new_goals:
                        st.error("Заполните все обязательные поля (отмечены *).")
                    else:
                        clients_module.update_client(
                            client["id"],
                            name=new_name.strip(),
                            social_link=new_social_link.strip(),
                            description=new_description.strip(),
                            tone_of_voice=new_tone,
                            goals=new_goals.strip(),
                        )
                        st.session_state[edit_key] = False
                        st.success("Изменения сохранены.")
                        st.rerun()
            with col2:
                if st.button("Отменить", key=f"cancel_btn_{client['id']}"):
                    st.session_state[edit_key] = False
                    st.rerun()


def render_clients_section() -> None:
    st.header("👤 Клиенты")
    st.write(
        "Добавьте клиентов, чтобы дальше генерировать для них контент-планы, сценарии, "
        "посты и рекламу. Все данные хранятся локально в файле `data/clients.json`."
    )

    _render_add_form()

    st.subheader("Список клиентов")
    all_clients = clients_module.list_clients()
    if not all_clients:
        st.info("Пока нет ни одного клиента — добавьте первого через форму выше.")
        return

    for client in all_clients:
        _render_client_card(client)

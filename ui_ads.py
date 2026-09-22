"""Раздел «Реклама»: генерация рекламных текстов для платных кампаний, список сохранённых
объявлений, ручное редактирование и удаление."""

import streamlit as st

from ads import AD_FORMAT_OPTIONS, delete_ad, generate_and_save_ad, list_ads, update_ad


def _render_generate_form(client: dict) -> None:
    client_id = client["id"]
    st.subheader("Сгенерировать новый рекламный текст")

    topic = st.text_input(
        "Тема / оффер рекламной кампании",
        placeholder="Например: скидка 20% на первую консультацию, запуск нового продукта",
        key="ad_topic_input",
    )
    ad_format = st.selectbox("Формат объявления", AD_FORMAT_OPTIONS, key="ad_format_select")

    if st.button("Сгенерировать рекламный текст", type="primary", key="generate_ad_button"):
        if not topic:
            st.error("Укажите тему / оффер кампании.")
        else:
            with st.spinner("Claude пишет рекламный текст..."):
                try:
                    generate_and_save_ad(client_id, topic, ad_format)
                    st.success("Рекламный текст сгенерирован и сохранён ниже.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Не удалось сгенерировать рекламный текст: {e}")


def _render_saved_ads(client_id: str) -> None:
    st.subheader("Сохранённые рекламные тексты")
    ads = list_ads(client_id)
    if not ads:
        st.info("Пока нет сохранённых рекламных текстов — сгенерируйте первый выше.")
        return

    for ad in ads:
        item_id = ad["id"]
        title = f"{ad.get('headline') or ad.get('topic', 'Без темы')} — {ad.get('format', '')}"
        with st.expander(title):
            headline = st.text_input("Заголовок", value=ad.get("headline", ""), key=f"ad_headline_{item_id}")
            body = st.text_area("Основной текст", value=ad.get("body", ""), height=200, key=f"ad_body_{item_id}")

            hooks = ad.get("hooks", [])
            st.write("**Варианты hook:**")
            new_hooks = []
            for i, hook in enumerate(hooks):
                new_hooks.append(st.text_input(f"Hook {i + 1}", value=hook, key=f"ad_hook_{item_id}_{i}"))

            cta = st.text_input("Призыв к действию (CTA)", value=ad.get("cta", ""), key=f"ad_cta_{item_id}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Сохранить изменения", key=f"ad_save_{item_id}"):
                    update_ad(client_id, item_id, headline=headline, body=body, hooks=new_hooks, cta=cta)
                    st.success("Изменения сохранены.")
                    st.rerun()
            with col2:
                if st.button("Удалить рекламный текст", key=f"ad_delete_{item_id}"):
                    delete_ad(client_id, item_id)
                    st.rerun()


def render_ads_section(client: dict) -> None:
    st.header("📣 Реклама")
    st.write(
        "Генерация рекламных текстов для платных кампаний: заголовок, основной текст, "
        "несколько вариантов hook и призыв к действию."
    )

    _render_generate_form(client)
    st.divider()
    _render_saved_ads(client["id"])

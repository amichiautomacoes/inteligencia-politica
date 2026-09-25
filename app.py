from __future__ import annotations

import streamlit as st

from hf_sync import data_files


st.set_page_config(
    page_title="Raio X do voto",
    layout="wide",
)


pages = [
    st.Page(
        "pages/raio_x_do_voto.py",
        title="Raio X do voto",
        default=True,
    ),
]


with st.sidebar:
    try:
        files = data_files()
    except Exception as exc:
        st.error(f"Falha ao ler HF: {exc}")
        files = []

    st.session_state["deputados_filters"] = {"ano": "2022", "cargo": "Todos", "nome": "Todos"}
    st.session_state["deputados_files"] = files

current_page = st.navigation(pages, position="sidebar")
current_page.run()

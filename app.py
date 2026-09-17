from __future__ import annotations

import streamlit as st

from hf_sync import data_files, path_filter_options


st.set_page_config(
    page_title="Raio X da Vota\u00e7\u00e3o",
    layout="wide",
)


pages = [
    st.Page(
        "pages/pagina_1.py",
        title="Raio X da Vota\u00e7\u00e3o",
        default=True,
    ),
]


with st.sidebar:
    try:
        files = data_files()
    except Exception as exc:
        st.error(f"Falha ao ler HF: {exc}")
        files = []

    options = path_filter_options(files)

    ano = st.selectbox("Ano", ["Todos", *options["anos"]], key="filtro_ano")
    cargo = st.selectbox("Cargo", ["Todos", *options["cargos"]], key="filtro_cargo")
    nome = st.selectbox("Nome", ["Todos", *options["nomes"]], key="filtro_nome")

    st.session_state["deputados_filters"] = {"ano": ano, "cargo": cargo, "nome": nome}
    st.session_state["deputados_files"] = files

current_page = st.navigation(pages, position="sidebar")
current_page.run()

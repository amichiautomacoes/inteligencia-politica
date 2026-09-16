from __future__ import annotations

import streamlit as st

from hf_sync import data_files, path_filter_options, sync_deputados


st.set_page_config(
    page_title="Visualizacao Eleitoral",
    layout="wide",
)


pages = [
    st.Page(
        "pages/pagina_1.py",
        title="Pagina 1",
        default=True,
    ),
    st.Page(
        "pages/pagina_2.py",
        title="Pagina 2",
    ),
]


with st.sidebar:
    st.divider()
    if st.button("Atualizar lista HF", use_container_width=True):
        st.session_state["force_hf_sync"] = True

    try:
        sync_info = sync_deputados(force=st.session_state.pop("force_hf_sync", False))
        st.caption(f"HF: {sync_info['remote']} ({sync_info['files']} arquivos)")
        files = data_files()
    except Exception as exc:
        st.error(f"Falha ao ler HF: {exc}")
        sync_info = None
        files = []

    options = path_filter_options(files)

    ano = st.selectbox("Ano", ["Todos", *options["anos"]], key="filtro_ano")
    cargo = st.selectbox("Cargo", ["Todos", *options["cargos"]], key="filtro_cargo")
    nome = st.selectbox("Nome", ["Todos", *options["nomes"]], key="filtro_nome")

    st.session_state["deputados_filters"] = {"ano": ano, "cargo": cargo, "nome": nome}
    st.session_state["deputados_files"] = files

current_page = st.navigation(pages, position="sidebar")
current_page.run()

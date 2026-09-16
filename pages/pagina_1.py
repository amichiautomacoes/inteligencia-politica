from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from hf_sync import data_files, file_by_kind, load_env, load_parquet, selected_deputado_files


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
BACKGROUND_PATH = ASSET_DIR / "background.png"


def _background_css() -> str:
    if not BACKGROUND_PATH.exists():
        return ""
    encoded = base64.b64encode(BACKGROUND_PATH.read_bytes()).decode("ascii")
    return f"""
    [data-testid="stAppViewContainer"] {{
        background-image:
            linear-gradient(100deg, rgba(3, 8, 20, 0.88) 0%, rgba(3, 8, 20, 0.75) 44%, rgba(3, 8, 20, 0.44) 100%),
            url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    """


def _apply_visual_model() -> None:
    st.markdown(
        f"""
        <style>
        {_background_css()}
        .stApp {{
            color: #eaf2ff;
        }}
        .stApp h1 {{
            font-size: 2.72rem;
            font-weight: 800;
            letter-spacing: 0.01em;
            color: #eaf2ff;
            margin-top: 0.1rem;
            margin-bottom: 0.15rem;
            line-height: 1.02;
        }}
        .stApp [data-testid="stCaptionContainer"] p {{
            color: #b7c7e6 !important;
            font-size: 0.95rem !important;
            margin-bottom: 1.1rem !important;
            line-height: 1.35 !important;
        }}
        .mapa-major-section,
        .mapa-section-card,
        .mapa-kpi-card,
        .raiox-kpi-card,
        .raiox-demografia-card,
        .raiox-heatmap-card {{
            border: 1px solid rgba(184, 208, 255, 0.24);
            box-shadow: 0 18px 40px rgba(2, 9, 24, 0.42);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
        }}
        .mapa-major-section {{
            position: relative;
            overflow: hidden;
            padding: 1.08rem 1.2rem 1.02rem 1.2rem;
            margin: 1.45rem 0 0.82rem 0;
            border-radius: 20px;
            background: linear-gradient(132deg, rgba(12, 29, 56, 0.88) 0%, rgba(9, 22, 43, 0.74) 54%, rgba(8, 20, 40, 0.56) 100%);
        }}
        .mapa-major-section::before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 6px;
            background: linear-gradient(180deg, rgba(191, 219, 254, 0.98) 0%, rgba(59, 130, 246, 0.92) 40%, rgba(11, 31, 77, 0.94) 100%);
            box-shadow: 0 0 26px rgba(96, 165, 250, 0.36);
        }}
        .mapa-major-section-title {{
            position: relative;
            z-index: 1;
            color: #f8fbff;
            font-size: 2.06rem;
            font-weight: 820;
            line-height: 1.04;
            letter-spacing: 0.01em;
        }}
        .mapa-major-section-subtitle {{
            position: relative;
            z-index: 1;
            max-width: 62rem;
            margin-top: 0.36rem;
            color: #d1def7;
            font-size: 0.96rem;
            line-height: 1.45;
        }}
        .mapa-section-card {{
            padding: 0.86rem 1rem 0.78rem 1rem;
            margin: 1.35rem 0 0.62rem 0;
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(7, 18, 36, 0.70) 0%, rgba(7, 18, 36, 0.52) 100%);
        }}
        .mapa-section-title {{
            color: #eaf2ff;
            font-size: 1.74rem;
            font-weight: 700;
            line-height: 1.06;
            letter-spacing: 0.01em;
        }}
        .mapa-section-subtitle {{
            margin-top: 0.17rem;
            color: #b7c7e6;
            font-size: 0.91rem;
        }}
        .mapa-kpi-grid,
        .raiox-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 0.45rem;
            margin-bottom: 0.9rem;
        }}
        .raiox-kpi-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
            margin-top: 0.95rem;
            margin-bottom: 1.1rem;
        }}
        .mapa-kpi-card,
        .raiox-kpi-card {{
            background: linear-gradient(145deg, rgba(10, 23, 45, 0.72) 0%, rgba(10, 23, 45, 0.48) 100%);
            border-radius: 16px;
            padding: 0.82rem 0.9rem 0.72rem 0.9rem;
            min-height: 7.8rem;
        }}
        .mapa-kpi-label {{
            color: #b7c7e6;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .mapa-kpi-value {{
            color: #f8fbff;
            font-size: 2.08rem;
            line-height: 1.04;
            font-weight: 800;
            margin-top: 0.2rem;
        }}
        .mapa-kpi-caption {{
            color: #b7c7e6;
            font-size: 0.8rem;
            margin-top: 0.34rem;
            line-height: 1.25;
        }}
        .raiox-kpi-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: rgba(239, 246, 255, 0.95);
        }}
        .raiox-kpi-dominant-label {{
            display: block;
            margin-top: 0.62rem;
            font-size: 1.58rem;
            font-weight: 800;
            color: #ffffff;
        }}
        .raiox-kpi-dominant-share,
        .raiox-kpi-value--persona {{
            display: block;
            margin-top: 0.28rem;
            font-size: 0.98rem;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.92);
        }}
        .raiox-demografia-card,
        .raiox-heatmap-card {{
            background: linear-gradient(145deg, rgba(7, 18, 36, 0.70) 0%, rgba(7, 18, 36, 0.52) 100%);
            border-radius: 18px;
            padding: 1rem 1.1rem 0.9rem 1.1rem;
            margin: 0.75rem 0 0.65rem 0;
        }}
        .raiox-demografia-header,
        .raiox-heatmap-title {{
            font-size: 1.9rem;
            font-weight: 800;
            line-height: 1.1;
            color: #f8fafc;
            letter-spacing: 0.01em;
        }}
        .raiox-demografia-subtitle,
        .raiox-heatmap-subtitle {{
            margin-top: 0.2rem;
            font-size: 1rem;
            color: rgba(226, 232, 240, 0.95);
        }}
        .raiox-heatmap-kpi-row {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.75rem;
        }}
        .raiox-heatmap-kpi {{
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 12px;
            padding: 0.72rem 0.8rem;
        }}
        .raiox-heatmap-kpi-label {{
            color: #b7c7e6;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .raiox-heatmap-kpi-value {{
            margin-top: 0.25rem;
            color: #ffffff;
            font-size: 1.16rem;
            font-weight: 800;
        }}
        [data-testid="stPlotlyChart"] {{
            background: linear-gradient(145deg, rgba(7, 18, 36, 0.72) 0%, rgba(7, 18, 36, 0.54) 100%);
            border: 1px solid rgba(184, 208, 255, 0.24);
            border-radius: 18px;
            padding: 0.56rem 0.66rem 0.3rem 0.66rem;
            box-shadow: 0 18px 40px rgba(2, 9, 24, 0.42);
        }}
        @media (max-width: 900px) {{
            .mapa-kpi-grid,
            .raiox-kpi-grid,
            .raiox-heatmap-kpi-row {{
                grid-template-columns: 1fr;
            }}
            .mapa-major-section-title {{
                font-size: 1.55rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _major_section_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="mapa-major-section">
            <div class="mapa-major-section-title">{title}</div>
            <div class="mapa-major-section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="mapa-section-card">
            <div class="mapa-section-title">{title}</div>
            <div class="mapa-section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _empty_map() -> go.Figure:
    fig = go.Figure(
        go.Scattermapbox(
            lat=[-18.9, -19.92, -21.76],
            lon=[-44.0, -43.94, -43.35],
            mode="markers",
            marker={"size": [18, 26, 14], "color": [32, 65, 44], "colorscale": "Blues", "opacity": 0.65},
            text=["Mapa territorial", "Parquet pendente", "Votos"],
            hoverinfo="text",
        )
    )
    fig.update_layout(
        mapbox={"style": "carto-darkmatter", "center": {"lat": -19.3, "lon": -44.2}, "zoom": 5.2},
        height=520,
        margin={"l": 0, "r": 0, "t": 18, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
    )
    return fig


def _format_number(value: float | int) -> str:
    return f"{float(value):,.0f}".replace(",", ".")


def _current_files() -> list[str]:
    files = st.session_state.get("deputados_files", [])
    if files:
        return files
    try:
        files = data_files()
        st.session_state["deputados_files"] = files
        return files
    except Exception as exc:
        st.error(f"Nao consegui ler a pasta `deputados` no HF: {exc}")
        return []


def _selected_files() -> list[str]:
    files = _current_files()
    filters = st.session_state.get("deputados_filters", {})
    selected = selected_deputado_files(files, filters)
    return selected or files


def _read_selected_parquet(kind: str) -> pd.DataFrame | None:
    file_name = file_by_kind(_selected_files(), kind)
    if not file_name:
        return None
    try:
        return load_parquet(file_name, load_env().get("HF_TOKEN"))
    except Exception as exc:
        st.warning(f"Nao consegui ler `{kind}.parquet`: {exc}")
        return None


def _render_kpis(df: pd.DataFrame | None) -> None:
    total_votos = "--"
    municipios = "--"
    reduto = "--"

    if df is not None and not df.empty:
        if "qt_votos" in df.columns:
            total_votos = _format_number(pd.to_numeric(df["qt_votos"], errors="coerce").fillna(0).sum())
        if "nm_municipio" in df.columns:
            municipios = _format_number(df["nm_municipio"].dropna().astype(str).str.strip().nunique())
        if {"nm_municipio", "qt_votos"}.issubset(df.columns):
            by_city = (
                df.assign(qt_votos=pd.to_numeric(df["qt_votos"], errors="coerce").fillna(0))
                .groupby("nm_municipio", as_index=False)["qt_votos"]
                .sum()
                .sort_values("qt_votos", ascending=False)
            )
            if not by_city.empty:
                reduto = str(by_city.iloc[0]["nm_municipio"]).title()

    st.markdown(
        f"""
        <div class="mapa-kpi-grid">
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Total de votos</div>
                <div class="mapa-kpi-value">{total_votos}</div>
                <div class="mapa-kpi-caption">Soma de qt_votos em votos_territoriais.</div>
            </div>
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Municipios</div>
                <div class="mapa-kpi-value">{municipios}</div>
                <div class="mapa-kpi-caption">Cobertura territorial do candidato.</div>
            </div>
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Principal reduto</div>
                <div class="mapa-kpi-value">{reduto}</div>
                <div class="mapa-kpi-caption">Municipio com maior votacao.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _mesorregiao_filter(df: pd.DataFrame | None) -> tuple[pd.DataFrame | None, str]:
    if df is None or df.empty or "nm_mesorregiao" not in df.columns:
        return df, "Todas"

    options = (
        df["nm_mesorregiao"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda values: values.ne("")]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    selected = st.selectbox(
        "Mesorregiao",
        ["Todas", *options],
        key="pagina1_mesorregiao",
    )
    if selected == "Todas":
        return df, selected
    return df[df["nm_mesorregiao"].astype(str).str.strip() == selected].copy(), selected


def _territorial_map(df: pd.DataFrame | None) -> go.Figure:
    required = {"nr_latitude", "nr_longitude", "qt_votos"}
    if df is None or df.empty or not required.issubset(df.columns):
        return _empty_map()

    map_df = df.copy()
    map_df["nr_latitude"] = pd.to_numeric(map_df["nr_latitude"], errors="coerce")
    map_df["nr_longitude"] = pd.to_numeric(map_df["nr_longitude"], errors="coerce")
    map_df["qt_votos"] = pd.to_numeric(map_df["qt_votos"], errors="coerce").fillna(0)
    map_df = map_df.dropna(subset=["nr_latitude", "nr_longitude"])
    map_df = map_df[map_df["qt_votos"] > 0].copy()
    if map_df.empty:
        return _empty_map()

    label_col = "nm_municipio" if "nm_municipio" in map_df.columns else None
    map_df["marker_size"] = np.clip(np.sqrt(map_df["qt_votos"]) * 2.2, 6, 34)
    center = {"lat": float(map_df["nr_latitude"].mean()), "lon": float(map_df["nr_longitude"].mean())}

    fig = go.Figure(
        go.Scattermapbox(
            lat=map_df["nr_latitude"],
            lon=map_df["nr_longitude"],
            mode="markers",
            marker={
                "size": map_df["marker_size"],
                "color": map_df["qt_votos"],
                "colorscale": "Blues",
                "opacity": 0.72,
                "showscale": True,
            },
            text=map_df[label_col].astype(str) if label_col else None,
            customdata=map_df[["qt_votos"]],
            hovertemplate="<b>%{text}</b><br>Votos: %{customdata[0]:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        mapbox={"style": "carto-darkmatter", "center": center, "zoom": 5.5},
        height=520,
        margin={"l": 0, "r": 0, "t": 18, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
    )
    return fig


def _territorial_treemap(df: pd.DataFrame | None) -> tuple[go.Figure, pd.DataFrame]:
    if df is None or df.empty or "qt_votos" not in df.columns:
        return _empty_treemap("Votacao territorial"), pd.DataFrame()

    group_cols = [col for col in ("nm_municipio", "nm_bairro") if col in df.columns]
    if not group_cols:
        return _empty_treemap("Votacao territorial"), pd.DataFrame()

    tree_df = df.copy()
    tree_df["qt_votos"] = pd.to_numeric(tree_df["qt_votos"], errors="coerce").fillna(0)
    for col in group_cols:
        tree_df[col] = tree_df[col].fillna("Nao informado").astype(str).str.strip()
        tree_df.loc[tree_df[col].eq(""), col] = "Nao informado"
    tree_df = (
        tree_df.groupby(group_cols, as_index=False)["qt_votos"]
        .sum()
        .sort_values("qt_votos", ascending=False)
        .head(500)
    )
    if tree_df.empty:
        return _empty_treemap("Votacao territorial"), pd.DataFrame()

    fig = px.treemap(tree_df, path=group_cols, values="qt_votos", title="Votacao por Municipio e Bairro")
    customdata = []
    ids = []
    for trace_id, label, parent in zip(fig.data[0].ids, fig.data[0].labels, fig.data[0].parents):
        parts = str(trace_id).split("/")
        municipio = parts[0] if parts else ""
        bairro = parts[1] if len(parts) > 1 else ""
        ids.append(str(trace_id))
        customdata.append([municipio, bairro, str(label), str(parent)])
    fig.update_traces(
        ids=ids,
        customdata=customdata,
        hovertemplate="<b>%{label}</b><br>Votos: %{value:,.0f}<extra></extra>",
    )
    fig.update_layout(
        height=430,
        margin={"l": 8, "r": 8, "t": 46, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
        title={"font": {"size": 18, "color": "#eaf2ff"}},
    )
    return fig, tree_df


def _empty_treemap(title: str) -> go.Figure:
    df = pd.DataFrame(
        {
            "grupo": ["Parquet pendente", "Parquet pendente", "Parquet pendente"],
            "item": ["Recorte A", "Recorte B", "Recorte C"],
            "valor": [45, 32, 23],
        }
    )
    fig = px.treemap(df, path=["grupo", "item"], values="valor", title=title)
    fig.update_layout(
        height=430,
        margin={"l": 8, "r": 8, "t": 46, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
        title={"font": {"size": 18, "color": "#eaf2ff"}},
    )
    return fig


def _demographic_label(column: str, prefix: str) -> str:
    label = column.removeprefix(prefix).replace("_", " ").strip()
    return label.title() if label else column


def _treemap_selection(event: object | None) -> dict[str, str]:
    if not event:
        return {}
    if hasattr(event, "selection"):
        selection = getattr(event, "selection")
    elif isinstance(event, dict):
        selection = event.get("selection", {})
    else:
        selection = {}

    if isinstance(selection, dict):
        points = selection.get("points", [])
    else:
        points = getattr(selection, "points", [])
    if not points:
        return {}

    point = points[0]
    if isinstance(point, dict):
        customdata = point.get("customdata") or []
        label = str(point.get("label") or "")
        parent = str(point.get("parent") or "")
    else:
        customdata = getattr(point, "customdata", []) or []
        label = str(getattr(point, "label", "") or "")
        parent = str(getattr(point, "parent", "") or "")
    if len(customdata) >= 2:
        municipio = str(customdata[0] or "")
        bairro = str(customdata[1] or "")
    else:
        municipio = parent or label
        bairro = "" if not parent else label

    selection: dict[str, str] = {}
    if municipio:
        selection["nm_municipio"] = municipio
    if bairro:
        selection["nm_bairro"] = bairro
    return selection


def _apply_territorial_context(df: pd.DataFrame, context: dict[str, str], mesorregiao: str) -> pd.DataFrame:
    result = df.copy()
    if mesorregiao != "Todas" and "nm_mesorregiao" in result.columns:
        result = result[result["nm_mesorregiao"].astype(str).str.strip() == mesorregiao]
    for column, value in context.items():
        if column in result.columns and value:
            result = result[result[column].astype(str).str.strip() == value]
    return result


def _demographic_bar(kind: str, context: dict[str, str], mesorregiao: str) -> go.Figure:
    df = _read_selected_parquet(kind)
    prefix_by_kind = {
        "genero": "votos_genero_",
        "idade": "votos_idade_",
        "escolaridade": "votos_escolaridade_",
        "estado_civil": "votos_estado_civil_",
    }
    prefix = prefix_by_kind[kind]

    if df is None or df.empty:
        bar_df = pd.DataFrame({"categoria": ["Parquet pendente"], "votos": [0]})
    else:
        df = _apply_territorial_context(df, context, mesorregiao)
        value_cols = [col for col in df.columns if col.startswith(prefix)]
        if value_cols:
            bar_df = pd.DataFrame(
                {
                    "categoria": [_demographic_label(col, prefix) for col in value_cols],
                    "votos": [pd.to_numeric(df[col], errors="coerce").fillna(0).sum() for col in value_cols],
                }
            ).sort_values("votos", ascending=True)
        else:
            bar_df = pd.DataFrame({"categoria": ["Colunas nao encontradas"], "votos": [0]})

    fig = px.bar(
        bar_df,
        x="votos",
        y="categoria",
        orientation="h",
        text="votos",
        title="Distribuicao por perfil no recorte selecionado",
        color="votos",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        height=430,
        margin={"l": 10, "r": 20, "t": 46, "b": 24},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
        title={"font": {"size": 18, "color": "#eaf2ff"}},
        xaxis={"title": "Votos", "gridcolor": "rgba(255,255,255,0.12)"},
        yaxis={"title": ""},
        coloraxis_showscale=False,
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    return fig


_apply_visual_model()

st.title("RaioX Votacao")
st.caption("Visualizacao conectada aos parquets selecionados por ano, cargo e deputado.")

votos_df = _read_selected_parquet("votos_territoriais")

_major_section_header("Mapa de Votacao", "Leitura territorial do desempenho eleitoral no recorte ativo.")
_render_kpis(votos_df)
_section_header("Distribuicao territorial dos votos", "Fonte: votos_territoriais.parquet.")
st.plotly_chart(_territorial_map(votos_df), use_container_width=True)

_section_header(
    "Votacao por Municipio e Perfil",
    "Treemap territorial e distribuicao demografica conforme parquet selecionado.",
)
treemap_df, mesorregiao = _mesorregiao_filter(votos_df)
col_left, col_right = st.columns(2, gap="large")
with col_left:
    treemap_fig, _ = _territorial_treemap(treemap_df)
    treemap_event = st.plotly_chart(
        treemap_fig,
        use_container_width=True,
        key="pagina1_treemap_territorial",
        on_select="rerun",
        selection_mode="points",
    )
    territorial_context = _treemap_selection(treemap_event)
with col_right:
    perfil_kind = st.selectbox(
        "Filtrar barras por",
        ["genero", "idade", "escolaridade", "estado_civil"],
        format_func=lambda value: value.replace("_", " ").title(),
        key="pagina1_bar_profile_kind",
    )
    if territorial_context:
        label = territorial_context.get("nm_bairro") or territorial_context.get("nm_municipio")
        st.caption(f"Recorte do treemap: {label}")
    st.plotly_chart(_demographic_bar(perfil_kind, territorial_context, mesorregiao), use_container_width=True)

_major_section_header("Perfil do Eleitor", "Perfil descritivo do eleitorado que sustentou esse voto.")

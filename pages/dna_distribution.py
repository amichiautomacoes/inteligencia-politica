"""Demographic distribution panel for the DNA Eleitoral page."""
from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


DIMENSIONS = {
    "Gênero": ("genero", "pct_genero_"),
    "Faixa etária": ("idade", "pct_idade_"),
    "Escolaridade": ("escolaridade", "pct_escolaridade_"),
    "Estado civil": ("estado_civil", "pct_estado_civil_"),
}


def _code(value: object) -> str:
    raw = str(value).strip()
    return raw.removesuffix(".0") if raw and raw.lower() != "nan" else ""


def _name(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    return re.sub(r"\s+", " ", "".join(c for c in normalized if not unicodedata.combining(c))).strip()


def _municipalities(votes: pd.DataFrame | None) -> list[tuple[str, str]]:
    if votes is None or votes.empty or "nm_municipio" not in votes:
        return []
    names = votes[["nm_municipio"]].copy()
    names["code"] = votes["cd_municipio"].map(_code) if "cd_municipio" in votes else ""
    names["nm_municipio"] = names["nm_municipio"].fillna("").astype(str).str.strip()
    names = names[names["nm_municipio"].ne("")].drop_duplicates()
    return sorted([(row.code, row.nm_municipio) for row in names.itertuples(index=False)], key=lambda item: item[1].casefold())


def _filter_municipality(df: pd.DataFrame, code: str, name: str) -> pd.DataFrame:
    if not name:
        return df
    if code and "cd_municipio" in df:
        matched = df.loc[df["cd_municipio"].map(_code).eq(code)]
        if not matched.empty:
            return matched.copy()
    if "nm_municipio" in df:
        return df.loc[df["nm_municipio"].map(_name).eq(_name(name))].copy()
    return df.iloc[:0].copy()


def _distribution(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    columns = [column for column in df if column.startswith(prefix)]
    if not columns:
        return pd.DataFrame(columns=["categoria", "percentual"])
    weight_col = "QT_VOTOS_TOTAL" if "QT_VOTOS_TOTAL" in df else "qt_votos"
    weights = pd.to_numeric(df[weight_col], errors="coerce").fillna(0).clip(lower=0) if weight_col in df else pd.Series(1.0, index=df.index)
    values = []
    for column in columns:
        percentages = pd.to_numeric(df[column], errors="coerce")
        valid = percentages.between(0, 100)
        if not valid.any():
            continue
        valid_weights = weights.loc[valid]
        average = (
            float((percentages.loc[valid] * valid_weights).sum() / valid_weights.sum())
            if valid_weights.sum() > 0 else float(percentages.loc[valid].mean())
        )
        if average > 0:
            values.append((column.removeprefix(prefix).replace("_", " ").capitalize(), average))
    result = pd.DataFrame(values, columns=["categoria", "percentual"])
    return result.sort_values("percentual", ascending=False) if not result.empty else result


def _votes_in_scope(votes: pd.DataFrame | None, code: str, name: str) -> float | None:
    if votes is None or votes.empty or "qt_votos" not in votes:
        return None
    frame = _filter_municipality(votes, code, name)
    return float(pd.to_numeric(frame["qt_votos"], errors="coerce").fillna(0).sum())


def render_electorate_distribution(read_parquet: Callable[[str], pd.DataFrame | None]) -> None:
    votes = read_parquet("votos_municipio")
    municipalities = _municipalities(votes)
    with st.container(border=True):
        st.markdown("#### Distribuição do eleitorado")
        st.caption("Participação estimada de cada categoria demográfica na votação do recorte selecionado.")
        chart_col, filter_col = st.columns([2.3, 1], gap="large")
        with filter_col:
            st.caption("Refine a distribuição")
            municipality_options = ["Todos os municípios"] + [name for _, name in municipalities]
            selected_name = st.selectbox("MUNICÍPIO", municipality_options, key="dna_distribution_municipality")
            dimension = st.selectbox("PERFIL DEMOGRÁFICO", list(DIMENSIONS), key="dna_distribution_dimension")
        code = ""
        name = ""
        if selected_name != "Todos os municípios":
            code, name = next(((code, name) for code, name in municipalities if name == selected_name), ("", ""))
        kind, prefix = DIMENSIONS[dimension]
        source = read_parquet(kind)
        with chart_col:
            if source is None or source.empty:
                st.info(f"Dados de {dimension.lower()} indisponíveis para este candidato.")
                return
            scoped = _filter_municipality(source, code, name)
            distribution = _distribution(scoped, prefix)
            if distribution.empty:
                st.info("Não há distribuição demográfica disponível para este recorte.")
                return
            total_votes = _votes_in_scope(votes, code, name)
            palette = ["#60A5FA", "#38BDF8", "#A78BFA", "#34D399", "#FBBF24", "#FB923C", "#94A3B8"]
            labels = distribution["categoria"].tolist()
            values = distribution["percentual"].tolist()
            estimated_votes = [value / 100 * total_votes for value in values] if total_votes is not None else None
            center = f"{total_votes:,.0f}".replace(",", ".") if total_votes is not None else "—"
            hover = (
                "<b>%{label}</b><br>%{value:.1f}% da distribuição<br>≈ %{customdata:,.0f} votos estimados<extra></extra>"
                if estimated_votes is not None else "<b>%{label}</b><br>%{value:.1f}% da distribuição<extra></extra>"
            )
            fig = go.Figure(go.Pie(
                labels=labels, values=values, hole=0.62, sort=False,
                marker={"colors": palette[:len(labels)], "line": {"color": "rgba(255,255,255,.25)", "width": 1}},
                customdata=estimated_votes, hovertemplate=hover,
                texttemplate="%{percent:.1%}", textposition="outside",
                textfont={"size": 12, "color": "#eaf2ff"},
            ))
            fig.update_layout(
                height=470, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#eaf2ff"}, margin={"l": 35, "r": 35, "t": 20, "b": 20},
                showlegend=True,
                legend={"orientation": "h", "x": 0.5, "xanchor": "center", "y": -0.08, "yanchor": "top", "font": {"color": "#eaf2ff"}},
                annotations=[{"x": 0.5, "y": 0.5, "text": f"<b>{html.escape(center)}</b><br><span style='font-size:13px'>votos no recorte</span>",
                              "showarrow": False, "font": {"size": 24, "color": "#f8fbff"}}],
            )
            st.plotly_chart(fig, use_container_width=True, key="dna_distribution_donut", config={"displayModeBar": False})
            st.caption("Os percentuais são estimativas de dimensões separadas; as categorias exibidas não representam cruzamentos entre perfis.")

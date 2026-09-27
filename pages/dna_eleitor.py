from __future__ import annotations

import html
from textwrap import dedent

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from hf_sync import file_by_kind, load_env, load_parquet
from pages.shared_header import (
    apply_shared_visual_model,
    major_section_header,
    render_page_header,
    selected_files,
    visualization_placeholder,
)


def _read_selected_parquet(kind: str) -> pd.DataFrame | None:
    file_name = file_by_kind(selected_files(), kind)
    if not file_name:
        return None
    try:
        return load_parquet(file_name, load_env().get("HF_TOKEN"))
    except Exception as exc:
        st.warning(f"Nao consegui ler `{kind}.parquet`: {exc}")
        return None


def _first_value(df: pd.DataFrame, column: str, fallback: str = "Nao informado") -> str:
    if df is None or df.empty or column not in df.columns:
        return fallback
    values = df[column].dropna()
    if values.empty:
        return fallback
    value = values.iloc[0]
    if isinstance(value, float) and pd.isna(value):
        return fallback
    text = str(value).strip()
    return text or fallback


def _format_percent_value(value: str, *, fraction: bool = False) -> str:
    if value in {"", "Nao informado"}:
        return "Nao informado"
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return "Nao informado"
    if fraction and abs(float(number)) <= 1:
        number = float(number) * 100
    return f"{float(number):.1f}%".replace(".", ",")


def _confidence_level(confidence_text: str) -> str:
    number = pd.to_numeric(pd.Series([confidence_text]), errors="coerce").iloc[0]
    if pd.isna(number):
        return "Nível não informado"
    confidence = float(number) * 100 if abs(float(number)) <= 1 else float(number)
    if confidence >= 80:
        return "Alta confiança"
    if confidence >= 60:
        return "Confiança moderada"
    return "Confiança baixa"


def _weighted_dominant(df: pd.DataFrame, value_col: str) -> tuple[str, float]:
    if df.empty or value_col not in df.columns:
        return "Nao informado", 0.0
    working = df[[value_col]].copy()
    working[value_col] = working[value_col].fillna("").astype(str).str.strip()
    working = working[working[value_col].ne("")]
    if working.empty:
        return "Nao informado", 0.0
    if "votos_candidato" in df.columns:
        working["votos_candidato"] = pd.to_numeric(
            df.loc[working.index, "votos_candidato"], errors="coerce"
        ).fillna(0)
    else:
        working["votos_candidato"] = 1
    grouped = working.groupby(value_col, as_index=False)["votos_candidato"].sum()
    total = float(grouped["votos_candidato"].sum())
    top = grouped.sort_values("votos_candidato", ascending=False).iloc[0]
    pct = float(top["votos_candidato"]) / total * 100 if total > 0 else 0.0
    return str(top[value_col]), pct


def _territorial_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Use a single territorial level: municipalities, or neighborhoods as fallback."""
    if "nivel_territorial" not in df:
        return df.copy()
    levels = df["nivel_territorial"].astype(str).str.strip().str.lower()
    for level in ("municipio", "bairro"):
        if levels.eq(level).any():
            return df.loc[levels.eq(level)].copy()
    return df.iloc[:0].copy()


def _demographic_percent(df: pd.DataFrame, column: str, category: str) -> float:
    pct_column = f"pct_{column}"
    if pct_column not in df or column not in df:
        return float("nan")
    # These percentages describe the category, not the profile's electoral share.
    rows = df.loc[df[column].eq(category)]
    values = pd.to_numeric(rows[pct_column], errors="coerce")
    valid = values.between(0, 100)
    if not valid.any():
        return float("nan")
    weights = pd.to_numeric(rows.loc[valid, "votos_candidato"], errors="coerce").fillna(0)
    return float((values[valid] * weights).sum() / weights.sum()) if weights.sum() > 0 else float(values[valid].mean())


def _icp_general_row(icp_df: pd.DataFrame) -> pd.DataFrame:
    if icp_df.empty:
        return icp_df
    working = _territorial_rows(icp_df)
    if "votos_candidato" not in working:
        working["votos_candidato"] = 0.0
    working["votos_candidato"] = pd.to_numeric(working["votos_candidato"], errors="coerce").fillna(0)

    persona, _ = _weighted_dominant(working, "persona_executiva")
    genero, pct_genero = _weighted_dominant(working, "genero_principal")
    idade, pct_idade = _weighted_dominant(working, "idade_principal")
    escolaridade, pct_escolaridade = _weighted_dominant(working, "escolaridade_principal")
    estado_civil, pct_estado_civil = _weighted_dominant(working, "estado_civil_principal")
    pct_genero = _demographic_percent(working, "genero_principal", genero)
    pct_idade = _demographic_percent(working, "idade_principal", idade)
    pct_escolaridade = _demographic_percent(working, "escolaridade_principal", escolaridade)
    pct_estado_civil = _demographic_percent(working, "estado_civil_principal", estado_civil)
    summary, _ = _weighted_dominant(working, "perfil_resumo")
    if summary == "Nao informado":
        summary = persona

    confidence = 0.0
    if "confianca_persona" in working.columns:
        confidence_values = pd.to_numeric(working["confianca_persona"], errors="coerce")
        if "votos_candidato" in working.columns:
            weights = pd.to_numeric(working["votos_candidato"], errors="coerce").fillna(0)
            valid = confidence_values.notna() & weights.gt(0)
            if valid.any():
                confidence = float((confidence_values[valid] * weights[valid]).sum() / weights[valid].sum())
        elif confidence_values.notna().any():
            confidence = float(confidence_values.mean())

    return pd.DataFrame(
        [
            {
                "persona_executiva": persona,
                "perfil_resumo": summary,
                "genero_principal": genero,
                "pct_genero_principal": pct_genero,
                "idade_principal": idade,
                "pct_idade_principal": pct_idade,
                "escolaridade_principal": escolaridade,
                "pct_escolaridade_principal": pct_escolaridade,
                "estado_civil_principal": estado_civil,
                "pct_estado_civil_principal": pct_estado_civil,
                "confianca_persona": confidence,
            }
        ]
    )


def _render_icp_geral_card(icp_df: pd.DataFrame | None) -> None:
    if icp_df is None or icp_df.empty:
        visualization_placeholder("ICP geral indisponivel")
        return

    icp_df = _icp_general_row(icp_df)
    persona = _first_value(icp_df, "persona_executiva", "Persona executiva dominante")
    confidence = _format_percent_value(_first_value(icp_df, "confianca_persona", "Nao informado"), fraction=True)
    confidence_level = _confidence_level(_first_value(icp_df, "confianca_persona", ""))
    summary = _first_value(icp_df, "perfil_resumo", "Resumo analitico da persona nao informado.")
    kpis = [
        ("🟢 Gênero principal", "genero_principal", "pct_genero_principal"),
        ("🔵 Faixa etária", "idade_principal", "pct_idade_principal"),
        ("🟣 Escolaridade", "escolaridade_principal", "pct_escolaridade_principal"),
        ("🟡 Estado civil", "estado_civil_principal", "pct_estado_civil_principal"),
    ]
    kpi_html = []
    for label, value_col, pct_col in kpis:
        value = _first_value(icp_df, value_col)
        pct = _format_percent_value(_first_value(icp_df, pct_col, ""))
        pct_html = "" if pct == "Nao informado" else f'<div class="dna-icp-kpi-pct">{html.escape(pct)}</div>'
        kpi_html.append(
            dedent(f"""
            <div class="dna-icp-kpi">
                <div class="dna-icp-kpi-label">{html.escape(label)}</div>
                <div class="dna-icp-kpi-value">{html.escape(value)}</div>
                {pct_html}
            </div>
            """)
        )

    st.html(
        dedent(f"""
        <div class="dna-icp-card">
            <div class="dna-icp-header">
                <div class="dna-icp-title">👤 {html.escape(persona)}</div>
                <div class="dna-icp-badges">
                    <div class="dna-icp-badge strong">Confiança {html.escape(confidence)}</div>
                    <div class="dna-icp-badge">{html.escape(confidence_level)}</div>
                </div>
            </div>
            <div class="dna-icp-summary">💬 {html.escape(summary)}</div>
            <div class="dna-icp-kpi-grid">
                {''.join(kpi_html)}
            </div>
        </div>
        """)
    )


def _sunburst_selection(event: object | None) -> dict[str, str]:
    if not event:
        return {}
    selection = getattr(event, "selection", {}) if hasattr(event, "selection") else event.get("selection", {}) if isinstance(event, dict) else {}
    points = selection.get("points", []) if isinstance(selection, dict) else getattr(selection, "points", [])
    if not points:
        return {}
    point = points[0]
    customdata = point.get("customdata") if isinstance(point, dict) else getattr(point, "customdata", None)
    if not customdata:
        return {}
    values = list(customdata) if not isinstance(customdata, str) else [customdata]
    return {
        "perfil_eleitor": str(values[0] or ""),
        "cluster_strategy_label": str(values[1] or ""),
        "persona_executiva": str(values[2] or ""),
        "cluster_strategy_reason": str(values[3] or ""),
    }


def _cluster_sunburst_frame(clusters_df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    if clusters_df is None or clusters_df.empty:
        return pd.DataFrame(), 0.0
    df = _territorial_rows(clusters_df)
    aliases = {
        "perfil_eleitor": ("perfil_eleitor", "perfil", "perfil_eleitoral"),
        "cluster_strategy_label": ("cluster_strategy_label", "cluster_label", "cluster"),
        "persona_executiva": ("persona_executiva", "persona", "persona_label"),
        "cluster_strategy_reason": ("cluster_strategy_reason", "cluster_reason", "justificativa"),
        "votos_candidato": ("votos_candidato", "votos", "total_votos"),
        "cd_municipio": ("cd_municipio", "codigo_municipio", "cod_municipio"),
    }
    for target, candidates in aliases.items():
        if target not in df.columns:
            source = next((column for column in candidates if column in df.columns), None)
            df[target] = df[source] if source else ""
    df["votos_candidato"] = pd.to_numeric(df["votos_candidato"], errors="coerce").fillna(0)
    for column in ("perfil_eleitor", "cluster_strategy_label", "persona_executiva", "cluster_strategy_reason"):
        df[column] = df[column].fillna("Nao informado").astype(str).str.strip().replace("", "Nao informado")

    municipality_total = float(df["votos_candidato"].sum())
    denominator = pd.to_numeric(df.get("total_votos_candidato", pd.Series(dtype=float)), errors="coerce").dropna()
    total_candidate = float(denominator.iloc[0]) if not denominator.empty else municipality_total
    df["share"] = pd.to_numeric(df["pct_market_share"], errors="coerce") if "pct_market_share" in df else df["votos_candidato"] / total_candidate * 100 if total_candidate else 0.0
    grouped = (
        df.groupby(["perfil_eleitor", "cluster_strategy_label", "persona_executiva", "cluster_strategy_reason"], dropna=False, as_index=False)[["votos_candidato", "share"]]
        .sum()
        .rename(columns={"votos_candidato": "votos"})
    )
    return grouped, float(municipality_total)


def _cluster_sunburst(df: pd.DataFrame, total_votes: float) -> go.Figure:
    if df.empty:
        return go.Figure()
    rows = [{"ids": "total", "labels": "Votação total", "parents": "", "values": total_votes, "custom": ["", "", "", "", float(df["share"].sum())]}]
    profile_totals = df.groupby("perfil_eleitor", as_index=False)[["votos", "share"]].sum()
    for _, row in profile_totals.iterrows():
        profile = str(row["perfil_eleitor"])
        rows.append({"ids": f"perfil::{profile}", "labels": profile, "parents": "total", "values": row["votos"], "custom": [profile, "", "", "", row["share"]]})
    for _, row in df.iterrows():
        profile = str(row["perfil_eleitor"])
        cluster = str(row["cluster_strategy_label"])
        persona = str(row["persona_executiva"])
        label = f"{cluster} · {persona}"
        rows.append({"ids": f"persona::{profile}::{cluster}::{persona}", "labels": label, "parents": f"perfil::{profile}", "values": row["votos"], "custom": [profile, cluster, persona, row["cluster_strategy_reason"], row["share"]]})
    chart = pd.DataFrame(rows)
    fig = go.Figure(go.Sunburst(ids=chart["ids"], labels=chart["labels"], parents=chart["parents"], values=chart["values"], customdata=chart["custom"], branchvalues="total", maxdepth=3, insidetextorientation="radial", textinfo="label+percent root", hovertemplate="%{label}<br>%{value:,.0f} votos<br>%{customdata[4]:.2f}% da votação geral<extra></extra>"))
    fig.update_layout(height=520, margin={"l": 8, "r": 8, "t": 18, "b": 8}, paper_bgcolor="rgba(0,0,0,0)", font={"color": "#eaf2ff"})
    return fig


def _render_cluster_sunburst(clusters_df: pd.DataFrame | None) -> None:
    grouped, total_votes = _cluster_sunburst_frame(clusters_df)
    if grouped.empty:
        visualization_placeholder("Composição do voto indisponível")
        return
    chart_col, detail_col = st.columns([1.6, 1], gap="large")
    with chart_col:
        st.markdown("<div class='raiox-chart-card-title'>Sunburst de composição do voto</div>", unsafe_allow_html=True)
        event = st.plotly_chart(_cluster_sunburst(grouped, total_votes), use_container_width=True, key="dna_cluster_sunburst", on_select="rerun", selection_mode="points")
    selected = _sunburst_selection(event)
    with detail_col:
        st.markdown("<div class='raiox-chart-card-title'>Detalhe do cluster selecionado</div>", unsafe_allow_html=True)
        if selected.get("persona_executiva"):
            st.markdown(f"**{html.escape(selected['cluster_strategy_label'])} · {html.escape(selected['persona_executiva'])}**", unsafe_allow_html=True)
            st.caption(f"Perfil: {selected['perfil_eleitor']}")
            st.info(selected.get("cluster_strategy_reason") or "Justificativa não informada.")
        else:
            st.caption("Selecione uma fatia do anel externo para ver a justificativa estratégica do cluster.")


def _heatmap_selection(event: object | None) -> dict[str, str]:
    if not event:
        return {}
    selection = getattr(event, "selection", {}) if hasattr(event, "selection") else event.get("selection", {}) if isinstance(event, dict) else {}
    points = selection.get("points", []) if isinstance(selection, dict) else getattr(selection, "points", [])
    if not points:
        return {}
    point = points[0]
    customdata = point.get("customdata") if isinstance(point, dict) else getattr(point, "customdata", None)
    if not customdata:
        return {}
    values = list(customdata) if not isinstance(customdata, str) else [customdata]
    return {
        "cluster": str(values[0] or ""),
        "dimension": str(values[1] or ""),
        "value": str(values[2] or ""),
        "label": str(values[3] or ""),
        "reason": str(values[4] or ""),
    }


def _heatmap_frame(df: pd.DataFrame | None, source: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    working = _territorial_rows(df)
    if working.empty:
        return pd.DataFrame()
    if "votos_candidato" not in working:
        working["votos_candidato"] = 0.0
    if source == "ICP geral":
        working["_profile"] = "ICP geral"
    elif "perfil_eleitor" in working:
        working["_profile"] = "ICP " + working["perfil_eleitor"].astype(str)
    else:
        return pd.DataFrame()
    rows = []
    for profile, group in working.groupby("_profile", sort=True):
        for dimension, column in [("Gênero", "genero_principal"), ("Faixa etária", "idade_principal"), ("Escolaridade", "escolaridade_principal"), ("Estado civil", "estado_civil_principal")]:
            category, _ = _weighted_dominant(group, column)
            pct = _demographic_percent(group, column, category)
            if pd.isna(pct):
                continue
            rows.append({"cluster": profile, "dimension": dimension, "value": category,
                         "pct_votos": pct, "strategy_label": _first_value(group, "cluster_strategy_label"),
                         "reason": _first_value(group, "cluster_strategy_reason", "Recomendação estratégica não informada para esta fonte."),
                         "source": source})
    return pd.DataFrame(rows)


def _heatmap_chart(df: pd.DataFrame) -> go.Figure:
    clusters = list(dict.fromkeys(df["cluster"].tolist()))
    dimensions = list(dict.fromkeys(df["dimension"].tolist()))
    pivot = df.pivot_table(index="dimension", columns="cluster", values="pct_votos", aggfunc="first").reindex(index=dimensions, columns=clusters)
    custom = []
    for dimension in dimensions:
        row = []
        for cluster in clusters:
            match = df[(df["dimension"] == dimension) & (df["cluster"] == cluster)]
            if match.empty:
                row.append([cluster, dimension, 0, "", ""])
            else:
                item = match.sort_values("pct_votos", ascending=False).iloc[0]
                row.append([cluster, dimension, item["value"], item["strategy_label"], item["reason"]])
        custom.append(row)
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=clusters,
        y=dimensions,
        customdata=custom,
        colorscale=[[0, "#0B1F4D"], [0.5, "#2563EB"], [1, "#EAF2FF"]],
        zmin=0, zmax=100, hoverongaps=False,
        colorbar={"title": "% no perfil"},
        hovertemplate="Cluster: %{x}<br>%{y}: %{customdata[2]}<br>%{z:.1f}% no perfil<extra></extra>",
    ))
    fig.update_layout(height=430, margin={"l": 12, "r": 12, "t": 18, "b": 70}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "#eaf2ff"}, xaxis={"tickangle": -35})
    return fig


def _render_cluster_heatmap(icp_general: pd.DataFrame | None, icp_clusters: pd.DataFrame | None) -> None:
    _, selector_col = st.columns([0.68, 0.32])
    with selector_col:
        source = st.selectbox("Base do heatmap", ["ICP geral", "ICP clusters"], key="dna_heatmap_source")
    selected_df = icp_general if source == "ICP geral" else icp_clusters
    heatmap_df = _heatmap_frame(selected_df, source)
    if heatmap_df.empty:
        visualization_placeholder("Heatmap demográfico indisponível")
        return
    chart_col, detail_col = st.columns([1.65, 1], gap="large")
    with chart_col:
        st.markdown("<div class='raiox-chart-card-title'>Mapa de calor / matriz de afinidade dos clusters</div>", unsafe_allow_html=True)
        event = st.plotly_chart(_heatmap_chart(heatmap_df), use_container_width=True, key="dna_cluster_heatmap", on_select="rerun", selection_mode="points")
    selected = _heatmap_selection(event)
    with detail_col:
        st.markdown("<div class='raiox-chart-card-title'>Recomendação tática</div>", unsafe_allow_html=True)
        if selected.get("cluster"):
            st.markdown(f"**{html.escape(selected['cluster'])}**")
            st.caption(f"{selected['dimension']}: {selected['value']} · {selected['label']}")
            st.info(selected.get("reason") or "Recomendação não informada.")
        else:
            st.caption("Clique em uma célula para ver o rótulo e a recomendação tática.")


apply_shared_visual_model()
render_page_header("dna")

DNA_SECTIONS = [
    (
        "Identidade da Base Eleitoral",
        "Quem é o eleitor-chave e quais atributos definem o perfil do seu eleitor.",
    ),
    (
        "Segmentação & Ação Tática",
        "Identificação de frentes de conversão, consolidação e expansão do eleitorado.",
    ),
    (
        "Matriz de Potencial Demográfico",
        "Comparativo entre o perfil do eleitor do candidato e a população local. Identificação de sobre-representação e frentes de expansão.",
    ),
    (
        "Expansão & Oportunidades para 2030",
        "Mapeamento em nível de bairro e área ponderada. Localização dos clusters táticos e visualização de manchas de potencial de crescimento.",
    ),
]


for index, (section_title, section_subtitle) in enumerate(DNA_SECTIONS):
    major_section_header(section_title, section_subtitle)
    if index == 0:
        icp_general_df = _read_selected_parquet("icp_geral")
        icp_clusters_df = _read_selected_parquet("icp_clusters")
        _render_icp_geral_card(icp_general_df)
        _render_cluster_sunburst(icp_clusters_df)
        _render_cluster_heatmap(icp_general_df, icp_clusters_df)
    else:
        visualization_placeholder()

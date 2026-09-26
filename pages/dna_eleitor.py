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


def _format_percent_value(value: str) -> str:
    if value in {"", "Nao informado"}:
        return "Nao informado"
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return value
    if abs(float(number)) <= 1:
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


def _icp_general_row(icp_df: pd.DataFrame) -> pd.DataFrame:
    if icp_df.empty:
        return icp_df
    working = icp_df.copy()
    if "votos_candidato" in working.columns:
        working["votos_candidato"] = pd.to_numeric(working["votos_candidato"], errors="coerce").fillna(0)
    if "nivel_territorial" in working.columns:
        municipio_rows = working[
            working["nivel_territorial"].astype(str).str.lower().str.strip().eq("municipio")
        ]
        if not municipio_rows.empty:
            working = municipio_rows.copy()

    if "cd_municipio" in working.columns and "votos_candidato" in working.columns:
        keep_cols = [
            col
            for col in (
                "cd_municipio",
                "nm_municipio",
                "persona_executiva",
                "perfil_resumo",
                "genero_principal",
                "idade_principal",
                "escolaridade_principal",
                "estado_civil_principal",
                "confianca_persona",
                "votos_candidato",
            )
            if col in working.columns
        ]
        working = working[keep_cols].copy()
        working = (
            working.sort_values("votos_candidato", ascending=False)
            .groupby("cd_municipio", as_index=False)
            .agg(
                {
                    **{
                        col: "first"
                        for col in keep_cols
                        if col not in {"cd_municipio", "votos_candidato"}
                    },
                    "votos_candidato": "sum",
                }
            )
        )

    persona, _ = _weighted_dominant(working, "persona_executiva")
    genero, pct_genero = _weighted_dominant(working, "genero_principal")
    idade, pct_idade = _weighted_dominant(working, "idade_principal")
    escolaridade, pct_escolaridade = _weighted_dominant(working, "escolaridade_principal")
    estado_civil, pct_estado_civil = _weighted_dominant(working, "estado_civil_principal")
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
    confidence = _format_percent_value(_first_value(icp_df, "confianca_persona", "Nao informado"))
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
    df = clusters_df.copy()
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

    # O total central deve contar cada município uma única vez, mesmo que o parquet
    # traga mais de uma linha de cluster para o mesmo município.
    if df["cd_municipio"].astype(str).str.strip().ne("").any():
        municipality_total = df.groupby("cd_municipio", as_index=False)["votos_candidato"].max()["votos_candidato"].sum()
    else:
        municipality_total = float(df["votos_candidato"].sum())
    grouped = (
        df.groupby(["perfil_eleitor", "cluster_strategy_label", "persona_executiva", "cluster_strategy_reason"], dropna=False, as_index=False)["votos_candidato"]
        .sum()
        .rename(columns={"votos_candidato": "votos"})
    )
    return grouped, float(municipality_total)


def _cluster_sunburst(df: pd.DataFrame, total_votes: float) -> go.Figure:
    if df.empty:
        return go.Figure()
    rows = [{"ids": "total", "labels": "Votação total", "parents": "", "values": total_votes, "custom": ["", "", "", ""]}]
    profile_totals = df.groupby("perfil_eleitor", as_index=False)["votos"].sum()
    for _, row in profile_totals.iterrows():
        profile = str(row["perfil_eleitor"])
        rows.append({"ids": f"perfil::{profile}", "labels": profile, "parents": "total", "values": row["votos"], "custom": [profile, "", "", ""]})
    for _, row in df.iterrows():
        profile = str(row["perfil_eleitor"])
        cluster = str(row["cluster_strategy_label"])
        persona = str(row["persona_executiva"])
        label = f"{cluster} · {persona}"
        rows.append({"ids": f"persona::{profile}::{cluster}::{persona}", "labels": label, "parents": f"perfil::{profile}", "values": row["votos"], "custom": [profile, cluster, persona, row["cluster_strategy_reason"]]})
    chart = pd.DataFrame(rows)
    fig = go.Figure(go.Sunburst(ids=chart["ids"], labels=chart["labels"], parents=chart["parents"], values=chart["values"], customdata=chart["custom"], branchvalues="total", maxdepth=3, insidetextorientation="radial", hovertemplate="%{label}<br>%{value:,.0f} votos<extra></extra>"))
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
    working = df.copy()
    aliases = {
        "perfil_eleitor": ("perfil_eleitor", "perfil", "perfil_eleitoral", "persona_executiva"),
        "pct_votos": ("pct_votos", "percentual_votos", "pct_votacao"),
        "votos_candidato": ("votos_candidato", "votos", "total_votos"),
        "cluster_strategy_label": ("cluster_strategy_label", "cluster_label", "cluster"),
        "cluster_strategy_reason": ("cluster_strategy_reason", "cluster_reason", "justificativa"),
    }
    for target, candidates in aliases.items():
        if target not in working.columns:
            column = next((candidate for candidate in candidates if candidate in working.columns), None)
            working[target] = working[column] if column else ""

    demographic_columns = [
        ("Gênero dominante", "genero_principal"),
        ("Faixa etária dominante", "idade_principal"),
        ("Escolaridade dominante", "escolaridade_principal"),
        ("Estado civil dominante", "estado_civil_principal"),
    ]
    available = [(label, column) for label, column in demographic_columns if column in working.columns]
    if not available:
        return pd.DataFrame()
    working["perfil_eleitor"] = working["perfil_eleitor"].fillna("Nao informado").astype(str).str.strip().replace("", "Nao informado")
    working["cluster_strategy_label"] = working["cluster_strategy_label"].fillna("Nao informado").astype(str).str.strip().replace("", "Nao informado")
    working["cluster_strategy_reason"] = working["cluster_strategy_reason"].fillna("Justificativa não informada.").astype(str).str.strip()
    working["votos_candidato"] = pd.to_numeric(working["votos_candidato"], errors="coerce").fillna(0)
    pct = pd.to_numeric(working["pct_votos"], errors="coerce")
    if pct.isna().all():
        total = working["votos_candidato"].sum()
        working["pct_votos"] = working["votos_candidato"] / total * 100 if total else 0
    else:
        working["pct_votos"] = pct.fillna(0)
        if working["pct_votos"].max() <= 1:
            working["pct_votos"] = working["pct_votos"] * 100

    rows: list[dict[str, object]] = []
    for label, column in available:
        values = working[column].fillna("Nao informado").astype(str).str.strip().replace("", "Nao informado")
        for index, value in values.items():
            rows.append({
                "cluster": working.at[index, "perfil_eleitor"],
                "dimension": label,
                "value": value,
                "pct_votos": float(working.at[index, "pct_votos"]),
                "strategy_label": working.at[index, "cluster_strategy_label"],
                "reason": working.at[index, "cluster_strategy_reason"],
                "source": source,
            })
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return (
        result.groupby(["cluster", "dimension", "value", "strategy_label", "reason", "source"], as_index=False)["pct_votos"]
        .sum()
    )


def _heatmap_chart(df: pd.DataFrame) -> go.Figure:
    clusters = list(dict.fromkeys(df["cluster"].tolist()))
    dimensions = list(dict.fromkeys(df["dimension"].tolist()))
    pivot = df.pivot_table(index="dimension", columns="cluster", values="pct_votos", aggfunc="sum", fill_value=0).reindex(index=dimensions, columns=clusters, fill_value=0)
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
        colorbar={"title": "% votos"},
        hovertemplate="Cluster: %{x}<br>%{y}: %{customdata[2]}<br>%{z:.1f}% dos votos<extra></extra>",
    ))
    fig.update_layout(height=430, margin={"l": 12, "r": 12, "t": 18, "b": 70}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "#eaf2ff"}, xaxis={"tickangle": -35})
    return fig


def _render_cluster_heatmap(icp_general: pd.DataFrame | None, icp_clusters: pd.DataFrame | None) -> None:
    selector_col, _ = st.columns([0.32, 0.68])
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

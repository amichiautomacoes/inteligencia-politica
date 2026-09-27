from __future__ import annotations

import html
from textwrap import dedent

import pandas as pd
import streamlit as st

from hf_sync import file_by_kind, load_env, load_parquet
from pages.cluster_cards import cluster_cards_html
from pages.dna_copy import sentence_label
from pages.demographic_comparison import render_comparison
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
        st.html('<div class="dna-icp-card"><h3 class="dna-subsection-title">Eleitor ideal do candidato</h3><p class="dna-subsection-description">Perfil geral indisponível para este candidato.</p></div>')
        return

    icp_df = _icp_general_row(icp_df)
    persona = _first_value(icp_df, "persona_executiva", "Persona executiva dominante")
    confidence = _format_percent_value(_first_value(icp_df, "confianca_persona", "Nao informado"), fraction=True)
    confidence_level = _confidence_level(_first_value(icp_df, "confianca_persona", ""))
    summary = _first_value(icp_df, "perfil_resumo", "Resumo analitico da persona nao informado.")
    persona = sentence_label(persona)
    summary = sentence_label(summary)
    normalize = lambda text: " ".join(text.casefold().split()).rstrip(".")
    summary_html = "" if normalize(summary) == normalize(persona) else f'<div class="dna-icp-summary">💬 {html.escape(summary)}</div>'
    kpis = [
        ("🟢 Gênero", "genero_principal", "pct_genero_principal"),
        ("🔵 Faixa etária", "idade_principal", "pct_idade_principal"),
        ("🟣 Escolaridade", "escolaridade_principal", "pct_escolaridade_principal"),
        ("🟡 Estado civil", "estado_civil_principal", "pct_estado_civil_principal"),
    ]
    kpi_html = []
    for label, value_col, pct_col in kpis:
        value = sentence_label(_first_value(icp_df, value_col))
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
            <h3 class="dna-subsection-title">Eleitor ideal do candidato</h3>
            <p class="dna-subsection-description">Síntese do perfil demográfico predominante na base eleitoral do candidato.</p>
            <div class="dna-icp-header">
                <div class="dna-icp-title">👤 {html.escape(persona)}</div>
                <div class="dna-icp-badges">
                    <div class="dna-icp-badge strong">Confiança do modelo: {html.escape(confidence)}</div>
                    <div class="dna-icp-badge">{html.escape(confidence_level)}</div>
                </div>
            </div>
            {summary_html}
            <div class="dna-icp-kpi-grid">
                {''.join(kpi_html)}
            </div>
            <p class="dna-subsection-note">Os percentuais indicam a participação de cada categoria dominante no perfil geral. As quatro dimensões são independentes e não somam 100%.</p>
        </div>
        """)
    )


def _cluster_profiles(clusters_df: pd.DataFrame | None) -> list[dict]:
    if clusters_df is None or clusters_df.empty:
        return []
    df = _territorial_rows(clusters_df)
    if df.empty or not {"perfil_eleitor", "votos_candidato"}.issubset(df.columns):
        return []
    df["votos_candidato"] = pd.to_numeric(df["votos_candidato"], errors="coerce").fillna(0)
    totals = pd.to_numeric(df.get("total_votos_candidato", pd.Series(dtype=float)), errors="coerce").dropna()
    total = float(totals.iloc[0]) if not totals.empty else float(df["votos_candidato"].sum())
    fallback = df["votos_candidato"] / total * 100 if total > 0 else pd.Series(0.0, index=df.index)
    df["share"] = pd.to_numeric(df["pct_market_share"], errors="coerce").fillna(fallback) if "pct_market_share" in df else fallback
    profiles = []
    for profile, group in df.groupby("perfil_eleitor", sort=True):
        demographics = []
        for label, column in [("Gênero", "genero_principal"), ("Faixa etária", "idade_principal"), ("Escolaridade", "escolaridade_principal"), ("Estado civil", "estado_civil_principal")]:
            category, _ = _weighted_dominant(group, column)
            demographics.append((label, category, _demographic_percent(group, column, category)))
        profiles.append({"id": str(profile), "classification": _first_value(group, "cluster_strategy_label").strip().upper(),
                         "persona": _first_value(group, "persona_executiva"),
                         "reason": _first_value(group, "cluster_strategy_reason", "Recomendação estratégica não informada."),
                         "votes": float(group["votos_candidato"].sum()), "share": float(group["share"].sum()),
                         "demographics": demographics})
    return profiles


def _render_cluster_profiles(clusters_df: pd.DataFrame | None) -> None:
    st.html(cluster_cards_html(_cluster_profiles(clusters_df)))


def _demographic_frame(df: pd.DataFrame | None, source: str) -> pd.DataFrame:
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


def _render_demographic_comparison(icp_general: pd.DataFrame | None, icp_clusters: pd.DataFrame | None) -> None:
    frames = [_demographic_frame(icp_general, "ICP geral"), _demographic_frame(icp_clusters, "ICP clusters")]
    render_comparison(pd.concat(frames, ignore_index=True))


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
        _render_cluster_profiles(icp_clusters_df)
        _render_demographic_comparison(icp_general_df, icp_clusters_df)
    else:
        visualization_placeholder()

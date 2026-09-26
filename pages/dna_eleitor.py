from __future__ import annotations

import html
from textwrap import dedent

import pandas as pd
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
        _render_icp_geral_card(_read_selected_parquet("icp_geral"))
    else:
        visualization_placeholder()

from __future__ import annotations

import base64
import html
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from hf_sync import data_files, file_by_kind, hf_filesystem, load_env, load_parquet, selected_deputado_files
from eleitoral.maps.dna_geo_reference import load_geo_reference
from eleitoral.maps.choropleth_maps import detailed_map, parliamentary_map, selected_context, territorial_map
from eleitoral.common.shared_header import render_page_header

try:
    import streamlit_shadcn_ui as ui
except Exception:
    ui = None


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
BACKGROUND_PATH = ASSET_DIR / "background.png"
DEMOGRAPHIC_CONTEXT_KEY = "pagina1_demographic_territorial_context"
EXPENSE_TREEMAP_KEY = "pagina1_treemap_despesas"
EXPENSE_SELECTION_KEY = "pagina1_tipo_despesa_selecionado"
EXPENSE_TREEMAP_REVISION_KEY = "pagina1_treemap_despesas_revisao"
USE_CUSTOM_KPI_CARDS = True


def _background_css() -> str:
    if not BACKGROUND_PATH.exists():
        return ""
    encoded = base64.b64encode(BACKGROUND_PATH.read_bytes()).decode("ascii")
    return f"""
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{encoded}");
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
        :root {{
            --raiox-card-bg: linear-gradient(145deg, rgba(11, 31, 77, 0.76) 0%, rgba(7, 24, 54, 0.68) 100%);
            --raiox-card-bg-soft: linear-gradient(145deg, rgba(11, 31, 77, 0.58) 0%, rgba(7, 24, 54, 0.48) 100%);
            --raiox-glass-bg: linear-gradient(145deg, rgba(15, 42, 88, 0.46) 0%, rgba(8, 28, 64, 0.32) 100%);
            --raiox-glass-bg-strong: linear-gradient(145deg, rgba(15, 42, 88, 0.58) 0%, rgba(8, 28, 64, 0.42) 100%);
            --raiox-control-bg: rgba(13, 39, 82, 0.72);
            --raiox-card-border: rgba(59, 130, 246, 0.24);
            --raiox-card-border-soft: rgba(177, 211, 255, 0.36);
            --raiox-outline-border: rgba(177, 211, 255, 0.34);
            --raiox-outline-border-strong: rgba(219, 234, 254, 0.48);
            --raiox-card-shadow: inset 0 1px 0 rgba(191, 219, 254, 0.08), 0 18px 40px rgba(2, 9, 24, 0.30);
            --raiox-glass-shadow: none;
        }}
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
        .raiox-hero {{
            position: relative;
            overflow: hidden;
            min-height: 22rem;
            margin: 0.15rem 0 1.25rem 0;
            padding: 2.05rem 2.35rem 2rem 2.35rem;
            border: 1px solid rgba(147, 197, 253, 0.24);
            border-radius: 0;
            background:
                linear-gradient(90deg, rgba(1, 10, 28, 0.96) 0%, rgba(3, 18, 45, 0.86) 46%, rgba(4, 20, 48, 0.60) 100%),
                url("data:image/png;base64,{base64.b64encode(BACKGROUND_PATH.read_bytes()).decode("ascii") if BACKGROUND_PATH.exists() else ""}");
            background-size: cover;
            background-position: center;
            box-shadow: 0 22px 54px rgba(1, 8, 24, 0.58);
        }}
        .raiox-hero-title {{
            position: relative;
            z-index: 1;
            max-width: calc(100% - 25rem);
            color: #f8fbff;
            font-size: 3.2rem;
            font-weight: 850;
            line-height: 1;
            letter-spacing: 0;
            text-shadow: 0 0 18px rgba(147, 197, 253, 0.36);
        }}
        .raiox-hero-subtitle {{
            position: relative;
            z-index: 1;
            margin-top: 1.1rem;
            max-width: calc(100% - 25rem);
            color: rgba(203, 213, 225, 0.82);
            font-size: 1.04rem;
            font-weight: 600;
        }}
        .raiox-candidate-row {{
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 10.5rem minmax(0, 1fr);
            gap: 1.35rem;
            align-items: center;
            margin-top: 1.5rem;
            max-width: 58rem;
        }}
        .raiox-candidate-photo {{
            width: 10.5rem;
            aspect-ratio: 1 / 1.35;
            border-radius: 10px;
            object-fit: cover;
            background: rgba(226, 232, 240, 0.92);
            border: 1px solid rgba(255,255,255,0.42);
            box-shadow: 0 16px 34px rgba(0,0,0,0.38);
        }}
        .raiox-candidate-info {{
            display: grid;
            gap: 1.35rem;
        }}
        .raiox-candidate-line {{
            color: #f8fbff;
            font-size: 1.72rem;
            font-weight: 850;
            line-height: 1.1;
            text-transform: uppercase;
            text-shadow: 0 0 16px rgba(147, 197, 253, 0.28);
        }}
        .raiox-page-switch {{
            position: absolute;
            z-index: 2;
            top: 2.05rem;
            right: 2.35rem;
            display: inline-grid;
            grid-template-columns: repeat(2, minmax(8.9rem, 1fr));
            gap: 0.25rem;
            padding: 0.28rem;
            border: 1px solid rgba(147, 197, 253, 0.32);
            border-radius: 999px;
            background: rgba(4, 18, 43, 0.72);
            box-shadow: inset 0 1px 0 rgba(219, 234, 254, 0.10), 0 12px 30px rgba(1, 8, 24, 0.30);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        .raiox-page-switch a {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 2.35rem;
            padding: 0 0.9rem;
            border-radius: 999px;
            color: #b7c7e6;
            font-size: 0.83rem;
            font-weight: 850;
            text-decoration: none;
            text-transform: uppercase;
            letter-spacing: 0;
            white-space: nowrap;
        }}
        .raiox-page-switch a.active {{
            color: #f8fbff;
            background: linear-gradient(145deg, rgba(96, 165, 250, 0.42), rgba(37, 99, 235, 0.30));
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.20), 0 8px 18px rgba(37, 99, 235, 0.24);
        }}
        .raiox-page-switch a:not(.active):hover {{
            color: #f8fbff;
            background: rgba(96, 165, 250, 0.16);
        }}
        @media (max-width: 900px) {{
            .raiox-page-switch {{
                position: relative;
                inset: auto;
                margin-bottom: 1.1rem;
                width: 100%;
                grid-template-columns: 1fr 1fr;
            }}
            .raiox-hero-title,
            .raiox-hero-subtitle {{
                max-width: 100%;
            }}
        }}
        @media (max-width: 760px) {{
            .raiox-hero {{
                padding: 1.45rem 1.1rem 1.4rem 1.1rem;
                min-height: auto;
            }}
            .raiox-hero-title {{
                font-size: 2.15rem;
            }}
            .raiox-candidate-row {{
                grid-template-columns: 7.5rem minmax(0, 1fr);
                gap: 0.95rem;
            }}
            .raiox-candidate-photo {{
                width: 7.5rem;
            }}
            .raiox-candidate-line {{
                font-size: 1.05rem;
            }}
            .raiox-page-switch {{
                grid-template-columns: 1fr;
                border-radius: 18px;
            }}
        }}
        .mapa-major-section,
        .mapa-section-card {{
            border: 1px solid var(--raiox-card-border);
            background: var(--raiox-card-bg);
            box-shadow: var(--raiox-card-shadow);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
        }}
        .mapa-kpi-card,
        .mapa-kpi-wide-card,
        .raiox-kpi-card,
        .raiox-demografia-card,
        .raiox-heatmap-card,
        .raiox-concentration-pill {{
            border: 1px solid var(--raiox-outline-border);
            background: transparent;
            box-shadow: none;
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
        }}
        .stApp [data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: var(--raiox-outline-border) !important;
            background: transparent !important;
            box-shadow: none;
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
        }}
        .mapa-major-section {{
            position: relative;
            overflow: hidden;
            padding: 1.28rem 1.35rem 1.16rem 1.52rem;
            margin: 1.78rem 0 1rem 0;
            border-radius: 20px;
            background:
                radial-gradient(circle at 14% 0%, rgba(96, 165, 250, 0.18) 0%, rgba(96, 165, 250, 0) 34%),
                linear-gradient(132deg, rgba(13, 36, 78, 0.94) 0%, rgba(9, 22, 43, 0.78) 54%, rgba(8, 20, 40, 0.58) 100%);
        }}
        .mapa-major-section::before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 9px;
            background: linear-gradient(180deg, rgba(248, 251, 255, 1) 0%, rgba(96, 165, 250, 0.98) 42%, rgba(37, 99, 235, 0.94) 100%);
            box-shadow: 0 0 34px rgba(96, 165, 250, 0.52);
        }}
        .mapa-major-section-title {{
            position: relative;
            z-index: 1;
            color: #f8fbff;
            font-size: 2.46rem;
            font-weight: 900;
            line-height: 1.02;
            letter-spacing: 0;
            text-shadow: 0 0 22px rgba(147, 197, 253, 0.34);
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
            background: var(--raiox-card-bg-soft);
        }}
        .mapa-section-title {{
            color: #eaf2ff;
            font-size: 1.54rem;
            font-weight: 760;
            line-height: 1.08;
            letter-spacing: 0;
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
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 0.95rem;
            margin-bottom: 1.1rem;
        }}
        .mapa-kpi-card,
        .mapa-kpi-wide-card,
        .raiox-kpi-card {{
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
        .mapa-kpi-wide-card {{
            position: relative;
            overflow: hidden;
            margin-top: -0.2rem;
            margin-bottom: 1.1rem;
            min-height: 9.4rem;
            padding: 1.18rem 1.35rem 1.05rem 1.35rem;
            background: transparent;
        }}
        .mapa-kpi-wide-tag {{
            position: absolute;
            top: 1rem;
            right: 1.2rem;
            color: #eaf2ff;
            background: transparent;
            border: 1px solid var(--raiox-outline-border);
            border-radius: 999px;
            padding: 0.38rem 0.78rem;
            font-size: 0.76rem;
            font-weight: 850;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        .mapa-kpi-wide-value {{
            max-width: 44rem;
            margin-top: 0.28rem;
            color: #ffffff;
            font-size: 2.35rem;
            font-weight: 900;
            line-height: 1.02;
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
        .raiox-kpi-dominant-share {{
            display: block;
            margin-top: 0.28rem;
            font-size: 0.98rem;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.92);
        }}
        .raiox-demografia-card,
        .raiox-heatmap-card {{
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
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.75rem;
        }}
        .raiox-heatmap-kpi {{
            background: transparent;
            border: 1px solid var(--raiox-outline-border);
            border-radius: 12px;
            padding: 0.72rem 0.8rem;
            box-shadow: none;
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
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
            background: transparent;
            border: 0;
            border-radius: 0;
            padding: 0;
            box-shadow: none;
        }}
        .raiox-bar-title {{
            color: #eaf2ff;
            font-size: 1.34rem;
            font-weight: 800;
            line-height: 1.12;
            margin: 0.12rem 0 0.35rem 0;
            text-align: center;
        }}
        .raiox-chart-card-title {{
            color: #eaf2ff;
            font-size: 1.34rem;
            font-weight: 800;
            line-height: 1.12;
            margin: 0.12rem 0 0.78rem 0;
            text-align: center;
        }}
        .raiox-neighborhood-kpis {{
            display: grid;
            gap: 0.45rem;
            max-width: 11rem;
            margin-left: auto;
        }}
        .raiox-neighborhood-kpi {{
            padding: 0.45rem 0.7rem;
            border: 1px solid rgba(96, 165, 250, 0.28);
            border-radius: 10px;
            background: rgba(11, 31, 77, 0.76);
            text-align: right;
        }}
        .raiox-neighborhood-kpi-label {{
            color: #b7c7e6;
            font-size: 0.72rem;
            line-height: 1.2;
        }}
        .raiox-neighborhood-kpi-value {{
            color: #f8fbff;
            font-size: 1.35rem;
            font-weight: 800;
            line-height: 1.15;
        }}
        .raiox-concentration-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin: 0.2rem 0 0.9rem;
            border-radius: 12px;
            background: rgba(7, 24, 54, 0.54);
            overflow: hidden;
        }}
        .raiox-concentration-pill {{
            padding: 1rem 1.15rem;
            border: 0 !important;
            border-right: 1px solid rgba(147, 197, 253, 0.16) !important;
            background: transparent;
            min-width: 0;
            display: flex;
            flex-direction: column;
        }}
        .raiox-concentration-pill:last-child {{
            border-right: 0 !important;
        }}
        .raiox-concentration-pill-label {{
            color: #9fb2d4;
            font-size: 0.7rem;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: 0.11em;
        }}
        .raiox-concentration-pill-value {{
            color: #f8fbff;
            font-size: clamp(1.55rem, 2vw, 2.1rem);
            font-weight: 800;
            line-height: 1.1;
            margin: 0.45rem 0 0.28rem;
            font-variant-numeric: tabular-nums;
        }}
        .raiox-concentration-pill-city {{
            color: #b7c7e6;
            font-size: 0.78rem;
            line-height: 1.3;
        }}
        .raiox-concentration-leader {{
            color: #f8fbff;
            font-size: 0.84rem;
            font-weight: 700;
            margin-top: 0.45rem;
        }}
        .raiox-concentration-track {{
            display: flex;
            height: 9px;
            flex: 0 0 9px;
            border-radius: 999px;
            background: rgba(147, 197, 253, 0.19);
            overflow: hidden;
        }}
        .raiox-concentration-fill {{
            height: 100%;
            background: #2563eb;
        }}
        .raiox-concentration-fill-new {{
            height: 100%;
            background: #7dd3fc;
        }}
        .raiox-concentration-bar-label {{
            color: #9fb2d4;
            font-size: 0.7rem;
            line-height: 1.3;
            margin: auto 0 0.3rem;
            padding-top: 0.9rem;
        }}
        .raiox-concentration-gain {{
            color: #93c5fd;
            font-size: 0.72rem;
            margin-top: 0.35rem;
        }}
        .raiox-concentration-reading {{
            color: #d6e4f9;
            font-size: 0.95rem;
            line-height: 1.5;
            margin: 0 0 0.7rem;
        }}
        .raiox-concentration-reading strong {{
            color: #f8fbff;
            font-weight: 750;
        }}
        .raiox-concentration-city-list {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.48rem 1rem;
            padding: 0.25rem 0 0.5rem;
            color: #eaf2ff;
            font-size: 0.83rem;
        }}
        .raiox-concentration-city-rank {{
            color: #93c5fd;
            font-weight: 750;
            margin-right: 0.35rem;
        }}
        .raiox-bar-filter [data-testid="stSelectbox"] {{
            max-width: 16rem;
            margin-left: auto;
        }}
        .stApp [data-testid="stSelectbox"] label,
        .stApp [data-testid="stMultiSelect"] label {{
            color: #dbeafe !important;
            font-weight: 700;
        }}
        .stApp [data-baseweb="select"] > div,
        .stApp [data-baseweb="select"] [role="combobox"],
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        .stApp [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
            background: var(--raiox-control-bg) !important;
            border: 1px solid rgba(125, 184, 255, 0.34) !important;
            border-radius: 12px !important;
            color: #f8fbff !important;
            box-shadow: inset 0 1px 0 rgba(219, 234, 254, 0.12), 0 10px 24px rgba(2, 9, 24, 0.20) !important;
            backdrop-filter: blur(12px) saturate(120%);
            -webkit-backdrop-filter: blur(12px) saturate(120%);
        }}
        .stApp [data-baseweb="select"] svg {{
            fill: #bfdbfe !important;
        }}
        .stApp [data-baseweb="select"] span,
        .stApp [data-baseweb="select"] div {{
            color: #f8fbff !important;
        }}
        div[data-baseweb="popover"] {{
            background: transparent !important;
        }}
        div[data-baseweb="popover"] ul,
        div[role="listbox"] {{
            background: linear-gradient(145deg, rgba(11, 31, 77, 0.96) 0%, rgba(7, 24, 54, 0.94) 100%) !important;
            border: 1px solid rgba(125, 184, 255, 0.34) !important;
            border-radius: 12px !important;
            box-shadow: 0 18px 42px rgba(2, 9, 24, 0.48) !important;
            color: #f8fbff !important;
        }}
        div[role="option"] {{
            background: transparent !important;
            color: #f8fbff !important;
        }}
        div[role="option"]:hover,
        div[role="option"][aria-selected="true"] {{
            background: rgba(59, 130, 246, 0.28) !important;
            color: #ffffff !important;
        }}
        @media (max-width: 900px) {{
            .mapa-kpi-grid,
            .raiox-kpi-grid,
            .raiox-heatmap-kpi-row {{
                grid-template-columns: 1fr;
            }}
            .raiox-concentration-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .raiox-concentration-pill:nth-child(2) {{
                border-right: 0 !important;
            }}
            .raiox-concentration-pill:nth-child(-n+2) {{
                border-bottom: 1px solid rgba(147, 197, 253, 0.16) !important;
            }}
            .raiox-concentration-city-list {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .mapa-major-section-title {{
                font-size: 1.55rem;
            }}
        }}
        @media (max-width: 600px) {{
            .raiox-concentration-city-list {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _major_section_header(title: str, subtitle: str) -> None:
    subtitle_html = (
        f'<div class="mapa-major-section-subtitle">{subtitle}</div>'
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div class="mapa-major-section">
            <div class="mapa-major-section-title">{title}</div>
            {subtitle_html}
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




def _load_geo_reference() -> tuple[dict | None, pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    return load_geo_reference()



def _normalize_municipio_name(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())




def _iter_geojson_rings(geometry: dict) -> list[list[list[float]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return coordinates
    if geometry_type == "MultiPolygon":
        return [ring for polygon in coordinates for ring in polygon]
    return []




def _format_number(value: float | int) -> str:
    return f"{float(value):,.0f}".replace(",", ".")


def _format_percent(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "--"
    return f"{float(value) * 100:.1f}%".replace(".", ",")


def _format_currency(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "R$ 0,00"
    formatted = f"{float(value):,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


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


def _selected_deputado_label() -> dict[str, str]:
    filters = st.session_state.get("deputados_filters", {})
    cargo = str(filters.get("cargo") or "Deputado").replace("_", " ").title()
    cargo_labels = {
        "Estaduais": "Deputado Estadual",
        "Federais": "Deputado Federal",
    }
    return {
        "nome": str(filters.get("nome") or "Todos").upper(),
        "cargo": cargo_labels.get(cargo, cargo).upper(),
        "ano": str(filters.get("ano") or "2022"),
    }


@st.cache_data(show_spinner=False)
def _remote_image_data_url(file_name: str, token: str | None = None) -> str:
    suffix = Path(file_name).suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    fs = hf_filesystem(token)
    with fs.open(file_name, "rb") as source:
        encoded = base64.b64encode(source.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _candidate_photo_data_url() -> str:
    image_file = next(
        (
            file_name
            for file_name in _selected_files()
            if Path(file_name).suffix.lower() in {".jpg", ".jpeg", ".png"}
        ),
        "",
    )
    if not image_file:
        return ""
    try:
        return _remote_image_data_url(image_file, load_env().get("HF_TOKEN"))
    except Exception:
        return ""


def _render_page_header() -> None:
    render_page_header("raio_x")


def _read_selected_parquet(kind: str) -> pd.DataFrame | None:
    file_name = file_by_kind(_selected_files(), kind)
    if not file_name:
        return None
    try:
        return load_parquet(file_name, load_env().get("HF_TOKEN"))
    except Exception as exc:
        st.warning(f"Nao consegui ler `{kind}.parquet`: {exc}")
        return None


def _territorial_kind_select() -> str:
    options = {
        "Mesorregião": "votos_mesorregiao",
        "Município": "votos_municipio",
    }
    selected = st.selectbox(
        "Filtro territorial",
        list(options.keys()),
        key="pagina1_territorial_kind",
    )
    return options[selected]


def _territorial_map_view(df: pd.DataFrame | None, kind: str) -> pd.DataFrame | None:
    if df is None or df.empty or "qt_votos" not in df.columns:
        return df
    if kind != "votos_mesorregiao" or "nm_mesorregiao" not in df.columns:
        return df

    group_cols = ["nm_mesorregiao"]
    optional_cols = [col for col in ("cd_mesorregiao", "nr_mesorregiao") if col in df.columns]
    result = (
        df.assign(qt_votos=pd.to_numeric(df["qt_votos"], errors="coerce").fillna(0))
        .groupby(group_cols, as_index=False)
        .agg({"qt_votos": "sum", **{col: "first" for col in optional_cols}})
    )
    result["nivel_territorial"] = "mesorregiao"
    return result


def _territorial_concentration_chart(df: pd.DataFrame | None, kind: str) -> go.Figure:
    label_col = "nm_mesorregiao" if kind == "votos_mesorregiao" else "nm_municipio"
    title = "Top 10 mesorregiões" if kind == "votos_mesorregiao" else "Top 10 municípios"

    if df is None or df.empty or "qt_votos" not in df.columns or label_col not in df.columns:
        ranking = pd.DataFrame({"territorio": ["Sem dados"], "qt_votos": [0.0], "pct": [0.0]})
    else:
        ranking = df.copy()
        ranking["qt_votos"] = pd.to_numeric(ranking["qt_votos"], errors="coerce").fillna(0)
        ranking[label_col] = ranking[label_col].fillna("Nao informado").astype(str).str.strip()
        ranking.loc[ranking[label_col].eq(""), label_col] = "Nao informado"
        ranking = (
            ranking.groupby(label_col, as_index=False)["qt_votos"]
            .sum()
            .sort_values("qt_votos", ascending=False)
            .head(10)
        )
        total_votes = float(pd.to_numeric(df["qt_votos"], errors="coerce").fillna(0).sum())
        ranking["pct"] = np.where(total_votes > 0, ranking["qt_votos"] / total_votes, 0.0)
        ranking = ranking.sort_values("qt_votos", ascending=True)
        ranking = ranking.rename(columns={label_col: "territorio"})

    ranking["qt_votos"] = pd.to_numeric(ranking["qt_votos"], errors="coerce").fillna(0)
    ranking["pct"] = pd.to_numeric(ranking["pct"], errors="coerce").fillna(0)
    max_votes = float(ranking["qt_votos"].max()) if not ranking.empty else 0.0
    if not np.isfinite(max_votes):
        max_votes = 0.0

    customdata = np.stack([ranking["qt_votos"], ranking["pct"]], axis=-1)
    trace_text = [
        f"{_format_number(votes)}<br><b>{_format_percent(pct)} dos votos</b>"
        for votes, pct in customdata
    ]
    fig = go.Figure(
        go.Bar(
            x=ranking["qt_votos"],
            y=ranking["territorio"],
            orientation="h",
            marker={
                "color": ranking["qt_votos"],
                "colorscale": [
                    [0.0, "rgba(96, 165, 250, 0.72)"],
                    [0.45, "rgba(37, 99, 235, 0.92)"],
                    [1.0, "rgba(147, 197, 253, 1.0)"],
                ],
                "line": {"color": "rgba(239,246,255,0.86)", "width": 1.2},
            },
            customdata=customdata,
            text=trace_text,
            textposition="auto",
            textfont={"color": "#f8fbff", "size": 12, "family": "Segoe UI, Inter, sans-serif"},
            insidetextfont={"color": "#ffffff", "size": 12, "family": "Segoe UI, Inter, sans-serif"},
            outsidetextfont={"color": "#f8fbff", "size": 12, "family": "Segoe UI, Inter, sans-serif"},
            cliponaxis=False,
            opacity=0.98,
            hovertemplate="<b>%{y}</b><br>Votos: %{customdata[0]:,.0f}<br>Participacao: %{customdata[1]:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        height=560,
        margin={"l": 200, "r": 28, "t": 58, "b": 22},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fbff", "family": "Segoe UI, Inter, sans-serif"},
        title={
            "text": title,
            "x": 0.0,
            "xanchor": "left",
            "font": {"size": 19, "color": "#f8fbff", "family": "Segoe UI, Inter, sans-serif"},
        },
        xaxis={
            "title": "",
            "showticklabels": False,
            "showgrid": False,
            "range": [0, max_votes * 1.12] if max_votes > 0 else None,
            "zeroline": False,
        },
        yaxis={
            "title": "",
            "tickfont": {"size": 11, "color": "#f8fbff"},
            "automargin": True,
            "ticks": "",
            "showgrid": False,
            "zeroline": False,
        },
        coloraxis_showscale=False,
        bargap=0.22,
    )
    return fig

def _municipal_concentration_frame(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty or not {"nm_municipio", "qt_votos"}.issubset(df.columns):
        return pd.DataFrame()

    result = df.copy()
    if "nivel_territorial" in result.columns:
        municipal = result[
            result["nivel_territorial"].astype(str).str.strip().str.lower().eq("municipio")
        ].copy()
        if not municipal.empty:
            result = municipal

    result["nm_municipio"] = result["nm_municipio"].fillna("").astype(str).str.strip()
    result["qt_votos"] = pd.to_numeric(result["qt_votos"], errors="coerce").fillna(0)
    result = result[result["nm_municipio"].ne("") & result["qt_votos"].gt(0)]
    if result.empty:
        return pd.DataFrame()

    agg_map = {"qt_votos": "sum"}
    if "qt_secoes_com_voto" in result.columns:
        result["qt_secoes_com_voto"] = pd.to_numeric(
            result["qt_secoes_com_voto"], errors="coerce"
        ).fillna(0)
        agg_map["qt_secoes_com_voto"] = "sum"

    result = (
        result.groupby("nm_municipio", as_index=False)
        .agg(agg_map)
        .sort_values("qt_votos", ascending=False)
        .reset_index(drop=True)
    )
    votos_total = float(result["qt_votos"].sum())
    if votos_total <= 0:
        return pd.DataFrame()

    result["rank_municipio"] = np.arange(1, len(result) + 1)
    result["pct_votos"] = result["qt_votos"] / votos_total
    result["votos_acumulados"] = result["qt_votos"].cumsum()
    result["pct_acumulado"] = result["votos_acumulados"] / votos_total
    return result


def _concentration_reference_rows(concentration_df: pd.DataFrame) -> pd.DataFrame:
    if concentration_df.empty:
        return pd.DataFrame()
    total_rows = len(concentration_df)
    points = [point for point in (1, 5, 10, 20, 50) if point <= total_rows]
    if total_rows not in points:
        points.append(total_rows)
    rows = concentration_df.iloc[[point - 1 for point in points]].copy()
    rows["referencia"] = [f"Top {point}" if point < total_rows else "Todos" for point in points]
    return rows


def _accumulated_concentration_chart(concentration_df: pd.DataFrame, max_rank: int | None = None) -> go.Figure:
    if concentration_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Dados municipais indisponiveis.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": "#eaf2ff", "size": 16},
        )
        fig.update_layout(height=390, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig

    chart_df = concentration_df.copy()
    if max_rank is not None and max_rank > 0:
        chart_df = chart_df[chart_df["rank_municipio"].le(max_rank)].copy()
    if chart_df.empty:
        chart_df = concentration_df.head(1).copy()

    ref_df = _concentration_reference_rows(chart_df)
    max_rank_value = int(chart_df["rank_municipio"].max())
    max_pct_value = float((chart_df["pct_acumulado"] * 100).max())
    y_axis_max = min(100, max(82, np.ceil((max_pct_value + 4) / 5) * 5))
    x_axis_padding = max(1.5, max_rank_value * 0.035)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_df["rank_municipio"],
            y=chart_df["pct_acumulado"] * 100,
            mode="lines",
            fill="tozeroy",
            line={"color": "#7DD3FC", "width": 3.4},
            fillcolor="rgba(59, 130, 246, 0.16)",
            customdata=np.stack(
                [
                    chart_df["votos_acumulados"],
                    chart_df["pct_acumulado"],
                    chart_df["nm_municipio"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>Top %{x:.0f} municípios</b><br>"
                "%{customdata[0]:,.0f} votos acumulados<br>"
                "%{customdata[1]:.1%} da votação total<br>"
                "Município na posição: %{customdata[2]}<extra></extra>"
            ),
            showlegend=False,
        )
    )
    if not ref_df.empty:
        marker_positions = []
        for rank in ref_df["rank_municipio"]:
            if int(rank) == 1:
                marker_positions.append("middle right")
            elif int(rank) == max_rank_value:
                marker_positions.append("middle left")
            else:
                marker_positions.append("top center")
        fig.add_trace(
            go.Scatter(
                x=ref_df["rank_municipio"],
                y=ref_df["pct_acumulado"] * 100,
                mode="markers+text",
                marker={
                    "size": 15,
                    "color": "#FFFFFF",
                    "line": {"color": "#38BDF8", "width": 3.5},
                    "symbol": "circle",
                },
                text=ref_df["referencia"],
                textposition=marker_positions,
                textfont={"color": "#FFFFFF", "size": 13, "family": "Segoe UI, Inter, sans-serif"},
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "%{customdata[0]:,.0f} votos acumulados<br>"
                    "%{customdata[1]:.1%} da votação total<extra></extra>"
                ),
                customdata=np.stack([ref_df["votos_acumulados"], ref_df["pct_acumulado"]], axis=-1),
                showlegend=False,
            )
        )
    fig.update_layout(
        height=430,
        margin={"l": 46, "r": 78, "t": 20, "b": 48},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff", "family": "Segoe UI, Inter, sans-serif"},
        xaxis={
            "title": "Municípios acumulados",
            "range": [0, max_rank_value + x_axis_padding],
            "gridcolor": "rgba(255,255,255,0.08)",
            "zeroline": False,
        },
        yaxis={
            "title": "% da Votação Total",
            "range": [0, y_axis_max],
            "ticksuffix": "%",
            "gridcolor": "rgba(255,255,255,0.12)",
            "zeroline": False,
        },
        shapes=[
            {
                "type": "rect",
                "xref": "paper",
                "x0": 0,
                "x1": 1,
                "yref": "y",
                "y0": 0,
                "y1": 80,
                "fillcolor": "rgba(56, 189, 248, 0.055)",
                "line": {"width": 0},
                "layer": "below",
            },
        ]
        + [
            {
                "type": "line",
                "xref": "paper",
                "x0": 0,
                "x1": 1,
                "yref": "y",
                "y0": level,
                "y1": level,
                "line": {
                    "color": "rgba(125, 211, 252, 0.72)" if level == 80 else "rgba(226, 232, 240, 0.16)",
                    "width": 2.4 if level == 80 else 1,
                    "dash": "solid" if level == 80 else "dot",
                },
            }
            for level in (25, 50, 75, 80)
        ],
        annotations=[
            {
                "xref": "paper",
                "x": 1.0,
                "xanchor": "right",
                "yref": "y",
                "y": level,
                "text": f"{level}%",
                "showarrow": False,
                "font": {
                    "color": "#E0F2FE" if level == 80 else "rgba(226, 232, 240, 0.72)",
                    "size": 12 if level == 80 else 10,
                },
                "bgcolor": "rgba(8, 47, 73, 0.82)" if level == 80 else "rgba(5, 12, 28, 0.62)",
                "borderpad": 3 if level == 80 else 2,
            }
            for level in (25, 50, 75, 80)
        ],
        hoverlabel={
            "bgcolor": "rgba(5,12,28,0.95)",
            "font_color": "#EAF2FF",
            "bordercolor": "rgba(147,197,253,0.55)",
        },
    )
    return fig


def _render_accumulated_concentration_section(df: pd.DataFrame | None) -> None:
    concentration_df = _municipal_concentration_frame(df)
    _major_section_header(
        "Concentração territorial dos votos",
        "Quanto da votação total está concentrada nos municípios onde o candidato mais recebeu votos.",
    )
    with st.container(border=True):
        if concentration_df.empty:
            st.warning("Nao encontrei dados municipais validos para calcular a concentracao territorial.")
            return

        def row_at(rank: int) -> pd.Series:
            idx = min(rank, len(concentration_df)) - 1
            return concentration_df.iloc[idx]

        def card_html(rank: int) -> str:
            row = row_at(rank)
            effective_rank = int(row["rank_municipio"])
            title = f"Top {rank}" if effective_rank >= rank else "Todos"
            percent = float(row["pct_acumulado"])
            previous_rank = {5: 1, 15: 5, 20: 15}.get(rank)
            previous_percent = float(row_at(previous_rank)["pct_acumulado"]) if previous_rank else 0.0
            previous_width = max(0, min(previous_percent, 100))
            gain_width = max(0, min(percent, 100) - previous_width)
            leader_html = (
                f'<div class="raiox-concentration-leader">{html.escape(str(row["nm_municipio"]).title())}</div>'
                if rank == 1 else ""
            )
            gain_html = (
                f'<div class="raiox-concentration-gain">+'
                f'{_format_percent(percent - previous_percent).removesuffix("%") } p.p. em relação ao Top {previous_rank}</div>'
                if rank != 1 else '<div class="raiox-concentration-gain">Município líder</div>'
            )
            return (
                '<div class="raiox-concentration-pill">'
                f'<div class="raiox-concentration-pill-label">{title}</div>'
                f'<div class="raiox-concentration-pill-value">{_format_percent(percent)}</div>'
                '<div class="raiox-concentration-pill-city">'
                f'{_format_number(float(row["votos_acumulados"]))} votos · '
                f'{effective_rank} {"município" if effective_rank == 1 else "municípios"}'
                "</div>"
                f'{leader_html}'
                f'{gain_html}'
                '<div class="raiox-concentration-bar-label">Participação na votação total</div>'
                '<div class="raiox-concentration-track">'
                f'<div class="raiox-concentration-fill" style="width: {previous_width:.2f}%"></div>'
                f'<div class="raiox-concentration-fill-new" style="width: {gain_width:.2f}%"></div>'
                '</div>'
                "</div>"
            )

        top1 = row_at(1)
        top15 = row_at(15)
        st.markdown(
            (
                '<div class="raiox-concentration-grid">'
                f"{card_html(1)}"
                f"{card_html(5)}"
                f"{card_html(15)}"
                f"{card_html(20)}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="raiox-concentration-reading">'
            f'<strong>{html.escape(str(top1["nm_municipio"]).title())}</strong> lidera com '
            f'<strong>{_format_percent(float(top1["pct_acumulado"]))}</strong>; '
            f'os 15 principais municípios concentram <strong>{_format_percent(float(top15["pct_acumulado"]))}</strong> dos votos.'
            '</p>',
            unsafe_allow_html=True,
        )
        for rank in (5, 15, 20):
            with st.expander(f"Ver municípios do Top {rank}"):
                city_items = "".join(
                    '<div>'
                    f'<span class="raiox-concentration-city-rank">{int(city_row["rank_municipio"]):02d}</span>'
                    f'{html.escape(str(city_row["nm_municipio"]).title())}'
                    '</div>'
                    for _, city_row in concentration_df.head(rank).iterrows()
                )
                st.markdown(
                    f'<div class="raiox-concentration-city-list">{city_items}</div>',
                    unsafe_allow_html=True,
                )
        max_rank = min(50, len(concentration_df))
        if len(concentration_df) > 50:
            st.caption(
                f"Visualização focada nos Top 50 de {_format_number(len(concentration_df))} municípios."
            )
        st.plotly_chart(
            _accumulated_concentration_chart(concentration_df, max_rank=max_rank),
            width="stretch",
        )


def _render_kpis(
    df: pd.DataFrame | None,
    context: dict[str, str] | None = None,
    mesorregiao: str = "Todas",
) -> None:
    total_votos = "--"
    municipios = "--"
    reduto_nome = "--"
    reduto_votos = "--"
    mesorregiao_nome = "--"
    mesorregiao_votos = "--"
    context = context or {}
    has_context = bool(context)
    votos_caption = "Votos nominais no recorte ativo." if has_context else "Votos nominais no recorte municipal."
    municipios_caption = "Municípios no recorte ativo." if has_context else "Municípios em que ele foi votado."

    if df is not None and not df.empty:
        metric_df = df
        if "nivel_territorial" in metric_df.columns:
            municipio_df = metric_df[
                metric_df["nivel_territorial"].astype(str).str.strip().str.lower() == "municipio"
            ].copy()
            if not municipio_df.empty:
                metric_df = municipio_df
        metric_df = _apply_territorial_context(metric_df, context, mesorregiao)

        if "qt_votos" in metric_df.columns:
            total_votos = _format_number(pd.to_numeric(metric_df["qt_votos"], errors="coerce").fillna(0).sum())
        if "nm_municipio" in metric_df.columns:
            municipios = _format_number(metric_df["nm_municipio"].dropna().astype(str).str.strip().nunique())
        if {"nm_municipio", "qt_votos"}.issubset(metric_df.columns):
            by_city = (
                metric_df.assign(qt_votos=pd.to_numeric(metric_df["qt_votos"], errors="coerce").fillna(0))
                .groupby("nm_municipio", as_index=False)["qt_votos"]
                .sum()
                .sort_values("qt_votos", ascending=False)
            )
            if not by_city.empty:
                reduto_nome = str(by_city.iloc[0]["nm_municipio"]).title()
                reduto_votos = _format_number(by_city.iloc[0]["qt_votos"])
        if {"nm_mesorregiao", "qt_votos"}.issubset(metric_df.columns):
            by_meso = (
                metric_df.assign(qt_votos=pd.to_numeric(metric_df["qt_votos"], errors="coerce").fillna(0))
                .groupby("nm_mesorregiao", as_index=False)["qt_votos"]
                .sum()
                .sort_values("qt_votos", ascending=False)
            )
            if not by_meso.empty:
                mesorregiao_nome = str(by_meso.iloc[0]["nm_mesorregiao"]).title()
                mesorregiao_votos = _format_number(by_meso.iloc[0]["qt_votos"])

    if ui is not None and not USE_CUSTOM_KPI_CARDS:
        kpi_cols = st.columns(3, gap="medium")
        cards = [
            {
                "label": "Total de votos",
                "value": total_votos,
                "description": votos_caption,
                "delta": "Recorte ativo" if has_context else "Base 2022",
                "key": "kpi_total_votos",
            },
            {
                "label": "Município mais votado",
                "value": reduto_votos,
                "description": reduto_nome,
                "delta": "No recorte" if has_context else "Reduto principal",
                "key": "kpi_municipio_mais_votado",
            },
            {
                "label": "Municípios com votos",
                "value": municipios,
                "description": municipios_caption,
                "delta": "Recorte ativo" if has_context else "Alcance municipal",
                "key": "kpi_municipios_com_votos",
            },
        ]
        for column, card in zip(kpi_cols, cards):
            with column:
                ui.metric_card(
                    label=card["label"],
                    value=card["value"],
                    description=card["description"],
                    delta=card["delta"],
                    variant="dashboard",
                    key=card["key"],
                )
        ui.metric_card(
            label="Território líder",
            value=mesorregiao_nome,
            description=f"{mesorregiao_votos} votos",
            delta="Maior concentração",
            variant="dashboard",
            key="kpi_territorio_lider",
        )
        return

    st.markdown(
        f"""
        <div class="mapa-kpi-grid">
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Total de votos</div>
                <div class="mapa-kpi-value">{total_votos}</div>
                <div class="mapa-kpi-caption">{votos_caption}</div>
            </div>
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Município mais votado</div>
                <div class="mapa-kpi-value">{reduto_votos}</div>
                <div class="mapa-kpi-caption">{html.escape(reduto_nome)}</div>
            </div>
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Municípios com votos</div>
                <div class="mapa-kpi-value">{municipios}</div>
                <div class="mapa-kpi-caption">{municipios_caption}</div>
            </div>
        </div>
        <div class="mapa-kpi-wide-card">
            <div class="mapa-kpi-wide-tag">Maior concentração</div>
            <div class="mapa-kpi-label">Território líder</div>
            <div class="mapa-kpi-wide-value">{html.escape(mesorregiao_nome)}</div>
            <div class="mapa-kpi-caption">{mesorregiao_votos} votos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _mesorregiao_filter(
    df: pd.DataFrame | None, municipal_votes: pd.DataFrame | None = None
) -> tuple[pd.DataFrame | None, str, str]:
    if df is None or df.empty:
        return df, "Todas", "Todos"

    votes = municipal_votes if municipal_votes is not None and not municipal_votes.empty else df
    votes = votes.copy()
    if "qt_votos" in votes.columns:
        votes["qt_votos"] = pd.to_numeric(votes["qt_votos"], errors="coerce").fillna(0)
    top_cities = (
        votes.groupby(["nm_mesorregiao", "nm_municipio"], as_index=False)["qt_votos"]
        .sum()
        .sort_values(["qt_votos", "nm_mesorregiao", "nm_municipio"], ascending=[False, True, True])
    ) if {"nm_mesorregiao", "nm_municipio", "qt_votos"}.issubset(votes.columns) else pd.DataFrame()
    meso_options = sorted(
        df["nm_mesorregiao"].dropna().astype(str).str.strip().loc[lambda s: s.ne("")].unique()
    ) if "nm_mesorregiao" in df.columns else []
    top_cities = top_cities[
        top_cities["nm_mesorregiao"].isin(meso_options)
    ] if not top_cities.empty else top_cities
    if not top_cities.empty:
        meso_totals = (
            top_cities.groupby("nm_mesorregiao", as_index=False)["qt_votos"]
            .sum()
            .sort_values(["qt_votos", "nm_mesorregiao"], ascending=[False, True])
        )
        default_meso = str(meso_totals.iloc[0]["nm_mesorregiao"])
    else:
        default_meso = "Todas"
    meso_choices = ["Todas", *meso_options]
    candidate_key = st.session_state.get("selected_deputado_key")
    if st.session_state.get("pagina1_demographic_candidate_key") != candidate_key:
        st.session_state["pagina1_demographic_candidate_key"] = candidate_key
        st.session_state["pagina1_mesorregiao"] = default_meso
        st.session_state.pop("pagina1_municipio", None)
    if st.session_state.get("pagina1_mesorregiao") not in meso_choices:
        st.session_state["pagina1_mesorregiao"] = default_meso
    mesorregiao = st.selectbox("Mesorregião", meso_choices, key="pagina1_mesorregiao")
    filtered = df if mesorregiao == "Todas" else df[
        df["nm_mesorregiao"].astype(str).str.strip().eq(mesorregiao)
    ].copy()

    city_options = sorted(
        filtered["nm_municipio"].dropna().astype(str).str.strip().loc[lambda s: s.ne("")].unique()
    ) if "nm_municipio" in filtered.columns else []
    city_choices = ["Todos", *city_options]
    eligible_cities = top_cities[
        top_cities["nm_mesorregiao"].eq(mesorregiao)
    ] if mesorregiao != "Todas" else top_cities
    eligible_cities = eligible_cities[eligible_cities["nm_municipio"].isin(city_options)]
    default_city = str(eligible_cities.iloc[0]["nm_municipio"]) if not eligible_cities.empty else "Todos"
    if st.session_state.get("pagina1_municipio") not in city_choices:
        st.session_state["pagina1_municipio"] = default_city
    municipio = st.selectbox("Município", city_choices, key="pagina1_municipio")
    if municipio != "Todos":
        filtered = filtered[filtered["nm_municipio"].astype(str).str.strip().eq(municipio)].copy()
    return filtered, mesorregiao, municipio








def _demographic_label(column: str, prefix: str) -> str:
    label = column.removeprefix(prefix).replace("_", " ").strip()
    return label.title() if label else column




def _neighborhood_vote_cards(
    municipal_votes: pd.DataFrame | None,
    neighborhood_votes: pd.DataFrame | None,
    municipio: str,
    context: dict[str, str],
) -> str:
    if municipio == "Todos" or neighborhood_votes is None or neighborhood_votes.empty:
        return ""

    municipal_rows = pd.DataFrame()
    if municipal_votes is not None and not municipal_votes.empty and "nm_municipio" in municipal_votes.columns:
        municipal_rows = municipal_votes[
            municipal_votes["nm_municipio"].astype(str).str.strip().eq(municipio)
        ]
    vote_source = municipal_rows if not municipal_rows.empty else neighborhood_votes
    city_votes = pd.to_numeric(vote_source["qt_votos"], errors="coerce").fillna(0).sum()
    cards = [
        f'<div class="raiox-neighborhood-kpi">'
        f'<div class="raiox-neighborhood-kpi-label">Votos no município</div>'
        f'<div class="raiox-neighborhood-kpi-value">{_format_number(city_votes)}</div>'
        f'</div>'
    ]
    if context.get("cd_area_ponderada") or context.get("cd_setor_censitario") or context.get("nm_bairro"):
        selected_rows = _apply_territorial_context(neighborhood_votes, context, "Todas", municipio)
        neighborhood_total = pd.to_numeric(selected_rows["qt_votos"], errors="coerce").fillna(0).sum()
        selected_label = context.get("nome_bairro") or "território selecionado"
        cards.append(
            f'<div class="raiox-neighborhood-kpi">'
            f'<div class="raiox-neighborhood-kpi-label">Votos em {html.escape(selected_label)}</div>'
            f'<div class="raiox-neighborhood-kpi-value">{_format_number(neighborhood_total)}</div>'
            f'</div>'
        )
    return '<div class="raiox-neighborhood-kpis">' + "".join(cards) + "</div>"


def _apply_territorial_context(
    df: pd.DataFrame, context: dict[str, str], mesorregiao: str, municipio: str = "Todos"
) -> pd.DataFrame:
    result = df.copy()
    if mesorregiao != "Todas" and "nm_mesorregiao" in result.columns:
        result = result[result["nm_mesorregiao"].astype(str).str.strip() == mesorregiao]
    if municipio != "Todos" and "nm_municipio" in result.columns:
        result = result[result["nm_municipio"].astype(str).str.strip() == municipio]
    for column in ("cd_municipio", "cd_bairro", "nm_municipio", "nm_bairro", "cd_area_ponderada", "cd_setor_censitario"):
        value = context.get(column)
        if column in result.columns and value:
            if column.startswith("cd_"):
                result = result[result[column].map(_territorial_code).eq(_territorial_code(value))]
            else:
                result = result[result[column].astype(str).str.strip().eq(value)]
    return result


def _territorial_code(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().removesuffix(".0")


def _section_context(key: str) -> dict[str, str]:
    context = st.session_state.setdefault(key, {})
    if not isinstance(context, dict):
        context = {}
        st.session_state[key] = context
    return {
        str(key): str(value)
        for key, value in context.items()
        if value not in (None, "")
    }


def _set_section_context(key: str, context: dict[str, str]) -> bool:
    normalized = {
        str(key): str(value)
        for key, value in context.items()
        if value not in (None, "")
    }
    if normalized == _section_context(key):
        return False
    st.session_state[key] = normalized
    return True


def _clear_section_context(key: str) -> None:
    st.session_state[key] = {}


def _context_label(context: dict[str, str]) -> str:
    return (
        (context.get("nome_bairro") or "território selecionado")
        if context.get("cd_area_ponderada") or context.get("cd_setor_censitario") or context.get("nm_bairro")
        else context.get("nm_municipio") or "recorte selecionado"
    )


def _demographic_bar(kind: str, context: dict[str, str], mesorregiao: str, municipio: str = "Todos") -> go.Figure:
    df = _read_selected_parquet(kind)
    prefix_by_kind = {
        "genero": "pct_genero_",
        "idade": "pct_idade_",
        "escolaridade": "pct_escolaridade_",
        "estado_civil": "pct_estado_civil_",
    }
    prefix = prefix_by_kind[kind]

    if df is None or df.empty:
        bar_df = pd.DataFrame({"categoria": ["Parquet pendente"], "percentual": [0.0]})
    else:
        df = _apply_territorial_context(df, context, mesorregiao, municipio)
        if (context.get("cd_area_ponderada") or context.get("cd_setor_censitario")) and "cd_bairro" in df.columns:
            area_votes = _read_selected_parquet("votos_bairro")
            if area_votes is not None and "cd_bairro" in area_votes.columns:
                area_rows = _apply_territorial_context(area_votes, context, mesorregiao, municipio)
                area_codes = {code for code in area_rows["cd_bairro"].map(_territorial_code) if code}
                df = df[df["cd_bairro"].map(_territorial_code).isin(area_codes)]
            else:
                df = df.iloc[0:0]
        value_cols = [col for col in df.columns if col.startswith(prefix)]
        if value_cols:
            weight_col = "QT_VOTOS_TOTAL" if "QT_VOTOS_TOTAL" in df.columns else "qt_votos"
            weights = pd.to_numeric(df.get(weight_col, 0), errors="coerce").fillna(0)
            total_weight = float(weights.sum())
            if total_weight > 0:
                percentages = [
                    (pd.to_numeric(df[col], errors="coerce").fillna(0) * weights).sum() / total_weight
                    for col in value_cols
                ]
            else:
                percentages = [
                    pd.to_numeric(df[col], errors="coerce").fillna(0).mean()
                    for col in value_cols
                ]
            bar_df = pd.DataFrame(
                {
                    "categoria": [_demographic_label(col, prefix) for col in value_cols],
                    "percentual": percentages,
                }
            ).sort_values("percentual", ascending=False)
        else:
            bar_df = pd.DataFrame({"categoria": ["Colunas nao encontradas"], "percentual": [0.0]})

    bar_df["percentual"] = pd.to_numeric(bar_df["percentual"], errors="coerce").fillna(0)
    bar_df["rotulo"] = bar_df["percentual"].map(lambda value: f"{value:.1f}%".replace(".", ","))

    fig = px.bar(
        bar_df,
        x="percentual",
        y="categoria",
        text="rotulo",
        color="percentual",
        color_continuous_scale="Blues",
        orientation="h",
    )
    max_percent = float(bar_df["percentual"].max() or 0)
    x_range = [0, min(110, max_percent * 1.18)] if max_percent > 0 else [0, 100]
    fig.update_layout(
        height=430,
        margin={"l": 180, "r": 88, "t": 8, "b": 42},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
        xaxis={
            "title": "% do perfil",
            "gridcolor": "rgba(255,255,255,0.12)",
            "range": x_range,
            "ticksuffix": "%",
        },
        yaxis={"title": "", "categoryorder": "total ascending"},
        coloraxis_showscale=False,
    )
    fig.update_traces(
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Participacao: %{x:.1f}%<extra></extra>",
    )
    return fig


def _campaign_total_votes(votos_df: pd.DataFrame | None) -> float:
    if votos_df is None or votos_df.empty or "qt_votos" not in votos_df.columns:
        return 0.0
    votes = pd.to_numeric(votos_df["qt_votos"], errors="coerce").fillna(0)
    if "nm_municipio" in votos_df.columns:
        frame = votos_df[["nm_municipio"]].copy()
        frame["qt_votos"] = votes
        return float(frame.groupby("nm_municipio")["qt_votos"].sum().sum())
    return float(votes.sum())


EXPENSE_TYPE_SHORT_LABELS = {
    "Atividades de militância e mobilização de rua": "Militância & Rua",
    "Publicidade por materiais impressos": "Materiais Impressos",
    "Despesa com Impulsionamento de Conteúdos": "MKT Digital",
    "Publicidade por adesivos": "Adesivos",
    "Correspondências e despesas postais": "Despesas Postais",
    "Serviços prestados por terceiros": "Serviços de Terceiros",
    "Cessão ou locação de veículos": "Veículos",
    "Locação/cessão de bens móveis (exceto veículos)": "Equipamentos",
    "Locação/cessão de bens imóveis": "Comitês",
    "Publicidade por jornais e revistas": "Jornais",
    "Comícios": "Comícios",
    "Diversas a especificar": "Outras Despesas",
    "Despesas com pessoal": "Equipe & Pessoal",
    "Combustíveis e lubrificantes": "Combustível",
    "Produção de jingles, vinhetas e slogans": "Jingles",
    "Encargos financeiros, taxas bancárias e/ou op. cartão de crédito": "Taxas",
}


def _short_expense_type_label(expense_type: str) -> str:
    label = EXPENSE_TYPE_SHORT_LABELS.get(expense_type)
    if label:
        return label
    if len(expense_type) <= 28:
        return expense_type
    return f"{expense_type[:25].rstrip()}..."


def _expense_cost_by_type_frame(
    despesas_df: pd.DataFrame | None,
    total_votes: float,
) -> pd.DataFrame:
    if (
        despesas_df is None
        or despesas_df.empty
        or "tipo_despesa" not in despesas_df.columns
        or "valor_despesa" not in despesas_df.columns
        or total_votes <= 0
    ):
        return pd.DataFrame()

    result = despesas_df[["tipo_despesa", "valor_despesa"]].copy()
    result["tipo_despesa"] = result["tipo_despesa"].fillna("Nao informado").astype(str).str.strip()
    result.loc[result["tipo_despesa"].eq(""), "tipo_despesa"] = "Nao informado"
    result["valor_total_despesa"] = pd.to_numeric(result["valor_despesa"], errors="coerce").fillna(0)
    result = (
        result.groupby("tipo_despesa", as_index=False)["valor_total_despesa"]
        .sum()
        .sort_values("valor_total_despesa", ascending=False)
    )
    result = result[result["valor_total_despesa"].gt(0)].copy()
    if result.empty:
        return result

    total_spend = float(result["valor_total_despesa"].sum())
    result["qt_votos"] = float(total_votes)
    result["custo_por_voto"] = result["valor_total_despesa"] / float(total_votes)
    result["pct_gasto"] = result["valor_total_despesa"] / total_spend if total_spend > 0 else 0.0
    result["pct_gasto_acumulado"] = result["pct_gasto"].cumsum()
    result["rotulo_custo"] = result["custo_por_voto"].map(_format_currency)
    result["tipo_despesa_curto"] = result["tipo_despesa"].map(_short_expense_type_label)
    result["rotulo_acumulado"] = result["pct_gasto_acumulado"].map(lambda value: f"{value:.0%}")
    result["rotulo_pct_gasto"] = result["pct_gasto"].map(lambda value: f"{value:.0%}")
    return result


def _cost_efficiency_kpis(chart_df: pd.DataFrame, selected_expense: str | None = None) -> dict[str, str]:
    if chart_df.empty:
        return {
            "custo_label": "Custo por voto (total geral)",
            "custo_por_voto": _format_currency(0),
            "gasto_label": "Total gasto",
            "total_gasto": _format_currency(0),
            "despesa_label": "Despesa líder",
            "despesa_lider": "Sem dados",
            "despesa_lider_caption": "Sem tipo de despesa",
        }
    filtered_df = chart_df
    if selected_expense:
        filtered_df = chart_df[chart_df["tipo_despesa"].eq(selected_expense)]
    total_spend = float(pd.to_numeric(filtered_df["valor_total_despesa"], errors="coerce").fillna(0).sum())
    total_votes = float(pd.to_numeric(chart_df["qt_votos"], errors="coerce").fillna(0).max())
    cost_per_vote = total_spend / total_votes if total_votes > 0 else 0.0
    leader = filtered_df.sort_values("valor_total_despesa", ascending=False).head(1).iloc[0]
    return {
        "custo_label": "Custo por voto" if selected_expense else "Custo por voto (total geral)",
        "custo_por_voto": _format_currency(cost_per_vote),
        "gasto_label": "Gasto no tipo selecionado" if selected_expense else "Total gasto",
        "total_gasto": _format_currency(total_spend),
        "despesa_label": "Tipo de despesa selecionado" if selected_expense else "Despesa líder",
        "despesa_lider": str(leader["tipo_despesa"]),
        "despesa_lider_caption": (
            f"{_format_currency(float(leader['valor_total_despesa']))} | "
            f"{_format_percent(float(leader['pct_gasto']))} do gasto"
        ),
    }


def _render_cost_efficiency_kpis(chart_df: pd.DataFrame, selected_expense: str | None = None) -> None:
    kpis = _cost_efficiency_kpis(chart_df, selected_expense)
    st.markdown(
        f"""
        <div class="raiox-heatmap-kpi-row">
            <div class="raiox-heatmap-kpi">
                <div class="raiox-heatmap-kpi-label">{html.escape(kpis["custo_label"])}</div>
                <div class="raiox-heatmap-kpi-value">{html.escape(kpis["custo_por_voto"])}</div>
            </div>
            <div class="raiox-heatmap-kpi">
                <div class="raiox-heatmap-kpi-label">{html.escape(kpis["gasto_label"])}</div>
                <div class="raiox-heatmap-kpi-value">{html.escape(kpis["total_gasto"])}</div>
            </div>
            <div class="raiox-heatmap-kpi">
                <div class="raiox-heatmap-kpi-label">{html.escape(kpis["despesa_label"])}</div>
                <div class="raiox-heatmap-kpi-value">{html.escape(kpis["despesa_lider"])}</div>
                <div class="mapa-kpi-caption">{html.escape(kpis["despesa_lider_caption"])}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _expense_cost_by_type_chart(chart_df: pd.DataFrame) -> go.Figure:
    if chart_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Dados de despesas de campanha indisponíveis.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": "#eaf2ff", "size": 16},
        )
        fig.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig

    display_df = chart_df.sort_values("valor_total_despesa", ascending=False).copy()
    fig = px.treemap(
        display_df,
        path=["tipo_despesa"],
        values="valor_total_despesa",
        custom_data=["tipo_despesa", "pct_gasto", "custo_por_voto"],
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{customdata[1]:.1%} do gasto",
        textfont={"color": "#f8fbff", "size": 14},
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Total gasto: R$ %{value:,.2f}<br>"
            "Participação no gasto: %{customdata[1]:.1%}<br>"
            "Custo por voto: R$ %{customdata[2]:,.2f}<extra></extra>"
        ),
        marker={"line": {"color": "rgba(191,219,254,0.55)", "width": 1}},
    )
    fig.update_layout(
        height=500,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff", "family": "Segoe UI, Inter, sans-serif"},
        hoverlabel={
            "bgcolor": "rgba(5,12,28,0.95)",
            "font_color": "#EAF2FF",
            "bordercolor": "rgba(147,197,253,0.55)",
        },
    )
    return fig


def _selected_expense_from_treemap(event: object | None, chart_df: pd.DataFrame) -> str | None:
    if not event:
        return None
    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection", {})
    points = getattr(selection, "points", None)
    if points is None and isinstance(selection, dict):
        points = selection.get("points", [])
    for point in points or []:
        customdata = point.get("customdata") if isinstance(point, dict) else getattr(point, "customdata", None)
        expense_type = str(customdata[0]) if customdata is not None and len(customdata) else ""
        if expense_type in chart_df["tipo_despesa"].values:
            return expense_type
    return None


def _territorial_expense_cost_frame(
    gastos_df: pd.DataFrame | None,
    expense_share: float,
    territory: str,
) -> pd.DataFrame:
    required = {"qt_votos", "valor_despesas_rateado", "nm_municipio", "nm_mesorregiao"}
    if gastos_df is None or gastos_df.empty or not required.issubset(gastos_df.columns):
        return pd.DataFrame()
    frame = gastos_df.copy()
    if "nivel_territorial" in frame.columns:
        levels = frame["nivel_territorial"].astype(str).str.strip().str.lower()
        if levels.eq("municipio").any():
            frame = frame[levels.eq("municipio")].copy()
        elif levels.eq("bairro").any():
            frame = frame[levels.eq("bairro")].copy()
        else:
            return pd.DataFrame()
    frame["qt_votos"] = pd.to_numeric(frame["qt_votos"], errors="coerce").fillna(0)
    frame["valor_despesas_rateado"] = pd.to_numeric(
        frame["valor_despesas_rateado"], errors="coerce"
    ).fillna(0)
    group_col = "nm_municipio" if territory == "Municípios" else "nm_mesorregiao"
    frame[group_col] = frame[group_col].fillna("Não informado").astype(str).str.strip()
    result = frame.groupby(group_col, as_index=False)[["qt_votos", "valor_despesas_rateado"]].sum()
    result = result[result["qt_votos"].gt(0)].copy()
    result["gasto_atribuido"] = result["valor_despesas_rateado"] * expense_share
    result["custo_por_voto"] = result["gasto_atribuido"] / result["qt_votos"]
    return result.sort_values("qt_votos", ascending=False)


def _territorial_expense_cost_chart(frame: pd.DataFrame, territory: str) -> go.Figure:
    fig = go.Figure()
    if frame.empty:
        fig.add_annotation(
            text="Dados territoriais de gastos indisponíveis.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            font={"color": "#eaf2ff", "size": 16},
        )
    else:
        label_col = "nm_municipio" if territory == "Municípios" else "nm_mesorregiao"
        display = frame.head(15 if territory == "Municípios" else len(frame)).iloc[::-1]
        fig.add_trace(go.Bar(
            x=display["custo_por_voto"],
            y=display[label_col],
            orientation="h",
            marker={"color": "#60a5fa"},
            customdata=display[["gasto_atribuido", "qt_votos"]].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>Custo por voto: R$ %{x:,.2f}<br>"
                "Gasto atribuído: R$ %{customdata[0]:,.2f}<br>"
                "Votos: %{customdata[1]:,.0f}<extra></extra>"
            ),
        ))
    fig.update_layout(
        height=470,
        margin={"l": 8, "r": 12, "t": 8, "b": 42},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
        xaxis={"title": "R$ por voto", "gridcolor": "rgba(255,255,255,0.10)", "rangemode": "tozero"},
        yaxis={"title": "", "automargin": True},
        showlegend=False,
    )
    return fig


def _render_cost_efficiency_section(
    votos_df: pd.DataFrame | None,
    despesas_df: pd.DataFrame | None,
    gastos_df: pd.DataFrame | None,
) -> None:
    _major_section_header(
        "Eficiência por Custo do Voto",
        "Participação de cada tipo de despesa nos gastos totais da campanha.",
    )
    chart_df = _expense_cost_by_type_frame(despesas_df, _campaign_total_votes(votos_df))
    selected_expense = st.session_state.get(EXPENSE_SELECTION_KEY)
    if chart_df.empty or selected_expense not in chart_df["tipo_despesa"].values:
        selected_expense = None
        st.session_state.pop(EXPENSE_SELECTION_KEY, None)
    _render_cost_efficiency_kpis(chart_df, selected_expense)
    cost_col, reserved_col = st.columns(2, gap="large")
    with cost_col:
        with st.container(border=True):
            st.markdown(
                "<div class='raiox-chart-card-title'>Gastos por tipo de despesa</div>",
                unsafe_allow_html=True,
            )
            treemap_event = st.plotly_chart(
                _expense_cost_by_type_chart(chart_df),
                width="stretch",
                key=f"{EXPENSE_TREEMAP_KEY}_{st.session_state.get(EXPENSE_TREEMAP_REVISION_KEY, 0)}",
                on_select="rerun",
                selection_mode="points",
            )
            clicked_expense = _selected_expense_from_treemap(treemap_event, chart_df)
            if clicked_expense and clicked_expense != selected_expense:
                st.session_state[EXPENSE_SELECTION_KEY] = clicked_expense
                st.rerun()
    with reserved_col:
        with st.container(border=True):
            title = selected_expense or "Gasto total"
            st.markdown(
                f"<div class='raiox-chart-card-title'>Custo por voto territorial · {html.escape(title)}</div>",
                unsafe_allow_html=True,
            )
            if selected_expense and st.button("Mostrar gasto total", key="pagina1_reset_tipo_despesa"):
                st.session_state.pop(EXPENSE_SELECTION_KEY, None)
                st.session_state[EXPENSE_TREEMAP_REVISION_KEY] = (
                    st.session_state.get(EXPENSE_TREEMAP_REVISION_KEY, 0) + 1
                )
                st.rerun()
            territory = st.radio(
                "Agrupar por", ["Municípios", "Mesorregiões"],
                horizontal=True, key="pagina1_custo_territorio",
            )
            share = 1.0
            if selected_expense:
                share = float(chart_df.loc[
                    chart_df["tipo_despesa"].eq(selected_expense), "pct_gasto"
                ].iloc[0])
            territorial_cost = _territorial_expense_cost_frame(gastos_df, share, territory)
            st.plotly_chart(
                _territorial_expense_cost_chart(territorial_cost, territory),
                width="stretch",
            )
            st.caption(
                "Gasto atribuído proporcionalmente aos votos em cada território. "
                "O parquet não identifica o tipo de despesa por local; por isso "
                "o custo por voto é igual entre territórios neste rateio."
            )


def _parliamentary_action_frame(
    votos_df: pd.DataFrame | None,
    emendas_df: pd.DataFrame | None,
) -> pd.DataFrame:
    if votos_df is None or votos_df.empty or emendas_df is None or emendas_df.empty:
        return pd.DataFrame()
    if "qt_votos" not in votos_df.columns:
        return pd.DataFrame()

    geojson_mg, df_tse_ref, df_municipios_ref, df_regioes_ref = _load_geo_reference()
    if geojson_mg is None or df_tse_ref is None or df_municipios_ref is None:
        return pd.DataFrame()

    code_col = next(
        (
            col
            for col in (
                "cd_ibge_municipio",
                "codigo_ibge",
                "CD_MUNICIPIO",
                "cd_municipio",
                "codigo_tse",
                "codigo_municipio_tse",
            )
            if col in votos_df.columns
        ),
        None,
    )
    city_col = "nm_municipio" if "nm_municipio" in votos_df.columns else None
    rank_col = next(
        (
            col
            for col in (
                "rank_municipio",
                "ranking_municipio",
                "posicao_municipio",
                "posicao_candidato_municipio",
                "rank_candidato_municipio",
                "ranking_candidato_municipio",
            )
            if col in votos_df.columns
        ),
        None,
    )
    extra_vote_cols = [rank_col] if rank_col else []

    if code_col == "cd_ibge_municipio" or code_col == "codigo_ibge":
        votos_base = votos_df[[code_col, "qt_votos"] + ([city_col] if city_col else []) + extra_vote_cols].copy()
        votos_base = votos_base.rename(columns={code_col: "codigo_ibge", city_col or code_col: "municipio"})
        votos_base["codigo_ibge"] = pd.to_numeric(votos_base["codigo_ibge"], errors="coerce").astype("Int64")
    elif code_col:
        votos_base = votos_df[[code_col, "qt_votos"] + ([city_col] if city_col else []) + extra_vote_cols].copy()
        votos_base = votos_base.rename(columns={code_col: "codigo_tse", city_col or code_col: "municipio"})
        votos_base["codigo_tse"] = pd.to_numeric(votos_base["codigo_tse"], errors="coerce").astype("Int64")
        votos_base = votos_base.merge(
            df_tse_ref[["codigo_tse", "codigo_ibge", "nome_municipio"]],
            on="codigo_tse",
            how="left",
        )
        votos_base["municipio"] = votos_base["municipio"].fillna(votos_base["nome_municipio"])
    elif city_col:
        votos_base = votos_df[[city_col, "qt_votos"] + extra_vote_cols].copy().rename(columns={city_col: "municipio"})
        votos_base["municipio_norm"] = votos_base["municipio"].map(_normalize_municipio_name)
        votos_base = votos_base.merge(
            df_tse_ref[["codigo_ibge", "nome_municipio", "municipio_norm"]],
            on="municipio_norm",
            how="left",
        )
    else:
        return pd.DataFrame()

    votos_base["qt_votos"] = pd.to_numeric(votos_base["qt_votos"], errors="coerce").fillna(0)
    agg_map = {"qt_votos": "sum", "municipio": "first"}
    if rank_col and rank_col in votos_base.columns:
        votos_base[rank_col] = pd.to_numeric(votos_base[rank_col], errors="coerce")
        agg_map[rank_col] = "min"
    votos_base = (
        votos_base.dropna(subset=["codigo_ibge"])
        .groupby("codigo_ibge", as_index=False)
        .agg(agg_map)
    )

    emenda_value_col = next(
        (
            col
            for col in ("valor_pago_atualizado", "valor_empenhado_ano", "valor_indicado")
            if col in emendas_df.columns
        ),
        None,
    )
    if emenda_value_col is None:
        return pd.DataFrame()

    emendas = emendas_df.copy()
    if "cd_ibge_municipio" in emendas.columns:
        emendas["codigo_ibge"] = pd.to_numeric(emendas["cd_ibge_municipio"], errors="coerce").astype("Int64")
    elif "nm_municipio" in emendas.columns:
        emendas["municipio_norm"] = emendas["nm_municipio"].map(_normalize_municipio_name)
        emendas = emendas.merge(
            df_tse_ref[["codigo_ibge", "municipio_norm"]],
            on="municipio_norm",
            how="left",
        )
    elif "municipio" in emendas.columns:
        emendas["municipio_norm"] = emendas["municipio"].map(_normalize_municipio_name)
        emendas = emendas.merge(
            df_tse_ref[["codigo_ibge", "municipio_norm"]],
            on="municipio_norm",
            how="left",
        )
    else:
        return pd.DataFrame()

    emendas[emenda_value_col] = pd.to_numeric(emendas[emenda_value_col], errors="coerce").fillna(0)
    extra_emenda_cols = [
        col
        for col in (
            "valor_total_emendas_municipio",
            "total_votos_municipio",
            "indice_retorno_parlamentar",
            "classificacao_retorno_parlamentar",
        )
        if col in emendas.columns
    ]
    emendas_agg = {emenda_value_col: "sum", **{col: "first" for col in extra_emenda_cols}}
    emendas_base = (
        emendas.dropna(subset=["codigo_ibge"])
        .groupby("codigo_ibge", as_index=False)
        .agg(emendas_agg)
        .rename(columns={emenda_value_col: "valor_emendas"})
    )

    result = df_municipios_ref.copy()
    result["codigo_ibge"] = pd.to_numeric(result["codigo_ibge"], errors="coerce").astype("Int64")
    result = result.dropna(subset=["codigo_ibge"]).merge(votos_base, on="codigo_ibge", how="left")
    result = result.merge(emendas_base, on="codigo_ibge", how="left")
    result["qt_votos"] = pd.to_numeric(result["qt_votos"], errors="coerce").fillna(0)
    if "total_votos_municipio" in result.columns:
        result["qt_votos"] = (
            pd.to_numeric(result["total_votos_municipio"], errors="coerce")
            .fillna(result["qt_votos"])
            .fillna(0)
        )
    if "valor_total_emendas_municipio" in result.columns:
        result["valor_emendas"] = (
            pd.to_numeric(result["valor_total_emendas_municipio"], errors="coerce")
            .fillna(result["valor_emendas"])
            .fillna(0)
        )
    result["valor_emendas"] = pd.to_numeric(result["valor_emendas"], errors="coerce").fillna(0)
    result["municipio"] = result["municipio"].fillna(result.get("nome"))
    if df_regioes_ref is not None and not df_regioes_ref.empty:
        result = result.merge(
            df_regioes_ref[["codigo_ibge", "mesorregiao_nome", "regiao_imediata_nome"]],
            on="codigo_ibge",
            how="left",
        )
    result["codigo_ibge_str"] = result["codigo_ibge"].astype("Int64").astype(str).str.zfill(7)
    result["municipio_exibicao"] = result["nome"].fillna(result["municipio"]).fillna("Município")
    result["municipio_contexto"] = result["municipio"].fillna(result["municipio_exibicao"]).astype(str)
    result["mesorregiao_exibicao"] = (
        result.get("mesorregiao_nome", pd.Series(index=result.index, dtype="object"))
        .fillna("Mesorregião não informada")
        .astype(str)
    )
    total_votes = float(result["qt_votos"].sum())
    result["pct_votos_total"] = np.where(total_votes > 0, result["qt_votos"] / total_votes, 0.0)
    if "indice_retorno_parlamentar" in result.columns:
        result["indice_retorno"] = pd.to_numeric(result["indice_retorno_parlamentar"], errors="coerce").fillna(0)
    else:
        result["indice_retorno"] = 0.0
    result["indice_retorno"] = pd.to_numeric(result["indice_retorno"], errors="coerce").replace([np.inf, -np.inf], 0).fillna(0)
    if rank_col and rank_col in result.columns:
        result["is_top3_vote"] = pd.to_numeric(result[rank_col], errors="coerce").le(3)
    else:
        top3_codes = set(result.nlargest(3, "qt_votos")["codigo_ibge"].dropna().astype("Int64").astype(str))
        result["is_top3_vote"] = result["codigo_ibge"].astype("Int64").astype(str).isin(top3_codes)

    result["categoria_coerencia"] = (
        result.get("classificacao_retorno_parlamentar", pd.Series(index=result.index, dtype="object"))
        .fillna("Sem Expressão")
        .astype(str)
        .str.strip()
    )
    result.loc[result["categoria_coerencia"].eq(""), "categoria_coerencia"] = "Sem Expressão"
    result["categoria_coerencia"] = result["categoria_coerencia"].replace(
        {
            "Sem Expressao": "Sem Expressão",
            "sem expressao": "Sem Expressão",
            "sem expressão": "Sem Expressão",
        }
    )
    no_emendas = result["valor_emendas"].le(0)
    result.loc[no_emendas & result["qt_votos"].gt(0), "categoria_coerencia"] = "Votos sem emendas"
    result.loc[no_emendas & result["qt_votos"].le(0), "categoria_coerencia"] = "Sem votos nem emendas"
    result["motivo_cor"] = result["categoria_coerencia"].map(
        {
            "Reduto Atendido": "Classificação de retorno parlamentar informada no parquet.",
            "Investimento": "Classificação de retorno parlamentar informada no parquet.",
            "Reduto Desassistido": "Classificação de retorno parlamentar informada no parquet.",
            "Sem Expressão": "Classificação de retorno parlamentar informada no parquet.",
            "Votos sem emendas": "O candidato recebeu votos neste município, mas não destinou emendas.",
            "Sem votos nem emendas": "O candidato não recebeu votos nem destinou emendas neste município.",
        }
    ).fillna("Classificação de retorno parlamentar informada no parquet.")
    return result




def _parliamentary_action_kpis(action_df: pd.DataFrame) -> dict[str, str]:
    if action_df.empty:
        return {
            "reciprocidade": "0,0%",
            "reciprocidade_caption": "Sem dados de emendas para calcular",
            "beneficiado": "Sem dados",
            "beneficiado_caption": "R$ 0,00 | 0 votos",
            "media_retorno": "R$ 0,00",
            "media_retorno_caption": "Média estadual por voto recebido",
        }

    total_emendas = float(pd.to_numeric(action_df["valor_emendas"], errors="coerce").fillna(0).sum())
    top3_emendas = float(
        pd.to_numeric(action_df.loc[action_df["is_top3_vote"], "valor_emendas"], errors="coerce").fillna(0).sum()
    )
    reciprocidade = top3_emendas / total_emendas if total_emendas > 0 else 0.0

    total_votes = float(pd.to_numeric(action_df["qt_votos"], errors="coerce").fillna(0).sum())
    media_retorno = total_emendas / total_votes if total_votes > 0 else 0.0

    beneficiary = action_df.sort_values("valor_emendas", ascending=False).head(1)
    if beneficiary.empty or float(beneficiary["valor_emendas"].iloc[0]) <= 0:
        beneficiado = "Sem emendas"
        beneficiado_caption = "R$ 0,00 | 0 votos"
    else:
        row = beneficiary.iloc[0]
        beneficiado = str(row.get("municipio_exibicao", "Município"))
        beneficiado_caption = (
            f"{_format_currency(float(row.get('valor_emendas', 0) or 0))} | "
            f"{_format_number(float(row.get('qt_votos', 0) or 0))} votos"
        )

    return {
        "reciprocidade": _format_percent(reciprocidade),
        "reciprocidade_caption": "Das emendas foram para municípios Top 3 do candidato",
        "beneficiado": beneficiado,
        "beneficiado_caption": beneficiado_caption,
        "media_retorno": _format_currency(media_retorno),
        "media_retorno_caption": "Valor médio de emendas por voto no estado",
    }


def _render_parliamentary_action_kpis(action_df: pd.DataFrame) -> None:
    kpis = _parliamentary_action_kpis(action_df)
    st.markdown(
        f"""
        <div class="raiox-kpi-grid">
            <div class="raiox-kpi-card">
                <div class="mapa-kpi-label">Taxa de Reciprocidade</div>
                <div class="mapa-kpi-value">{html.escape(kpis["reciprocidade"])}</div>
                <div class="mapa-kpi-caption">{html.escape(kpis["reciprocidade_caption"])}</div>
            </div>
            <div class="raiox-kpi-card">
                <div class="mapa-kpi-label">Maior Beneficiado (R$)</div>
                <div class="mapa-kpi-value">{html.escape(kpis["beneficiado"])}</div>
                <div class="mapa-kpi-caption">{html.escape(kpis["beneficiado_caption"])}</div>
            </div>
            <div class="raiox-kpi-card">
                <div class="mapa-kpi-label">Média R$/Voto</div>
                <div class="mapa-kpi-value">{html.escape(kpis["media_retorno"])}</div>
                <div class="mapa-kpi-caption">{html.escape(kpis["media_retorno_caption"])}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _parliamentary_map_selection(event: object | None) -> dict[str, str]:
    if event is None:
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
    customdata = point.get("customdata") if isinstance(point, dict) else getattr(point, "customdata", None)
    if customdata is None or len(customdata) < 9:
        return {}
    return {
        "nm_municipio": str(customdata[8]),
    }


def _render_parliamentary_action_section(
    votos_df: pd.DataFrame | None,
    emendas_df: pd.DataFrame | None,
) -> None:
    _major_section_header(
        "Mapa da atuação parlamentar de acordo com os votos",
        "Índice de Retorno Parlamentar: valor total de emendas no município dividido pelos votos recebidos.",
    )
    _section_header(
        "Coerência política territorial",
        "Mapa por categoria: azul indica reduto atendido, verde indica investimento, amarelo marca reduto desassistido, laranja indica baixa expressão, cinza marca votos sem emendas e branco indica ausência de votos e emendas.",
    )
    action_df = _parliamentary_action_frame(votos_df, emendas_df)
    _render_parliamentary_action_kpis(action_df)
    with st.container(border=True):
        fig = parliamentary_map(action_df)
        if fig is not None:
            st.plotly_chart(fig, width="stretch", height=610, key="pagina1_parliamentary_action_map")
        else:
            st.info("Mapa parlamentar indisponível.")


_apply_visual_model()

_render_page_header()

_major_section_header("Mapa Territorial da Votação", "Leitura territorial do desempenho eleitoral no recorte ativo.")
votos_municipio_df = _read_selected_parquet("votos_municipio")
votos_bairro_df = _read_selected_parquet("votos_bairro")
_render_kpis(votos_municipio_df, {})
header_col, filter_col = st.columns([0.72, 0.28], gap="large")
with header_col:
    _section_header(
        "Sua votação no território de Minas Gerais",
        "Concentração territorial dos votos por mesorregião e por município.",
    )
with filter_col:
    territorial_kind = _territorial_kind_select()
votos_df = _territorial_map_view(_read_selected_parquet(territorial_kind), territorial_kind)
map_col, concentration_col = st.columns([0.60, 0.40], gap="large")
with map_col:
    with st.container(border=True):
        fig = territorial_map(votos_df, territorial_kind)
        if fig is not None:
            st.plotly_chart(fig, width="stretch", height=560, key="pagina1_territorial_map")
        else:
            st.info("Mapa territorial indisponível.")
with concentration_col:
    with st.container(border=True):
        st.markdown(
            "<div class='raiox-chart-card-title'>Concentração territorial</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _territorial_concentration_chart(votos_df, territorial_kind),
            width="stretch",
        )
_section_header(
    "Votação por Setor Censitário e Perfil Demográfico",
    "Votação por setor censitário do IBGE, com nome do bairro associado e perfil demográfico do recorte selecionado.",
)
neighborhood_df, mesorregiao, municipio = _mesorregiao_filter(votos_bairro_df, votos_municipio_df)
current_filters = (mesorregiao, municipio)
if st.session_state.get("pagina1_demographic_filter_context") not in (None, current_filters):
    _clear_section_context(DEMOGRAPHIC_CONTEXT_KEY)
    st.session_state["pagina1_bairro_mapa_revisao"] = (
        st.session_state.get("pagina1_bairro_mapa_revisao", 0) + 1
    )
st.session_state["pagina1_demographic_filter_context"] = current_filters
col_left, col_right = st.columns(2, gap="large")
with col_left:
    with st.container(border=True):
        title_col, cards_col = st.columns([0.56, 0.44], gap="small")
        with title_col:
            st.markdown(
                "<div class='raiox-chart-card-title'>Votação por setor censitário</div>",
                unsafe_allow_html=True,
            )
        with cards_col:
            cards_html = _neighborhood_vote_cards(
                votos_municipio_df, neighborhood_df, municipio,
                _section_context(DEMOGRAPHIC_CONTEXT_KEY),
            )
            if cards_html:
                st.markdown(cards_html, unsafe_allow_html=True)
        municipality_codes = pd.to_numeric(neighborhood_df.get("cd_ibge_municipio", pd.Series(dtype=str)), errors="coerce").dropna()
        neighborhood_fig, map_note = (
            detailed_map(neighborhood_df, int(municipality_codes.mode().iloc[0]))
            if municipio != "Todos" and not municipality_codes.empty
            else (None, "Selecione um município com votos para ver o mapa.")
        )
        if neighborhood_fig is not None:
            map_event = st.plotly_chart(
                neighborhood_fig,
                width="stretch", height=500,
                key=f"pagina1_bairro_mapa_{st.session_state.get('pagina1_bairro_mapa_revisao', 0)}",
                on_select="rerun",
                selection_mode="points",
            )
            selection_context = selected_context(map_event)
            if selection_context and _set_section_context(DEMOGRAPHIC_CONTEXT_KEY, selection_context):
                st.rerun()
        if map_note:
            st.caption(map_note)
        demographic_context = _section_context(DEMOGRAPHIC_CONTEXT_KEY)
        if demographic_context.get("bairros"):
            st.caption(f"Bairros eleitorais associados: {demographic_context['bairros']}")
with col_right:
    with st.container(border=True):
        st.markdown(
            "<div class='raiox-bar-title'>Distribuição por perfil demográfico</div>",
            unsafe_allow_html=True,
        )
        _, bar_filter_col = st.columns([0.54, 0.46], gap="medium")
        with bar_filter_col:
            st.markdown("<div class='raiox-bar-filter'>", unsafe_allow_html=True)
            perfil_kind = st.selectbox(
                "Filtrar barras por",
                ["genero", "idade", "escolaridade", "estado_civil"],
                format_func=lambda value: value.replace("_", " ").title(),
                key="pagina1_bar_profile_kind",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)
        demographic_context = _section_context(DEMOGRAPHIC_CONTEXT_KEY)
        st.plotly_chart(
            _demographic_bar(perfil_kind, demographic_context, mesorregiao, municipio),
            width="stretch",
        )
        if demographic_context:
            label = _context_label(demographic_context)
            st.caption(f"Recorte territorial ativo: {label}")
            if st.button("Limpar recorte territorial", key="pagina1_clear_territorial_context"):
                _clear_section_context(DEMOGRAPHIC_CONTEXT_KEY)
                st.session_state["pagina1_bairro_mapa_revisao"] = (
                    st.session_state.get("pagina1_bairro_mapa_revisao", 0) + 1
                )
                st.rerun()

_render_accumulated_concentration_section(votos_municipio_df)
emendas_legislativa_df = _read_selected_parquet("emendas_legislativa")
_render_parliamentary_action_section(votos_municipio_df, emendas_legislativa_df)
despesas_campanha_df = _read_selected_parquet("despesas_campanha")
gastos_territoriais_df = _read_selected_parquet("gastos_territoriais")
_render_cost_efficiency_section(votos_municipio_df, despesas_campanha_df, gastos_territoriais_df)




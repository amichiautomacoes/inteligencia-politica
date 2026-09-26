from __future__ import annotations

import base64
import html
import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from hf_sync import data_files, file_by_kind, hf_filesystem, load_env, load_parquet, selected_deputado_files


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
BACKGROUND_PATH = ASSET_DIR / "background.png"


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
        .mapa-kpi-wide-card,
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
        .mapa-kpi-wide-card {{
            position: relative;
            overflow: hidden;
            margin-top: -0.2rem;
            margin-bottom: 1.1rem;
            min-height: 9.4rem;
            padding: 1.18rem 1.35rem 1.05rem 1.35rem;
            background:
                linear-gradient(90deg, rgba(3, 14, 36, 0.92) 0%, rgba(5, 24, 55, 0.74) 62%, rgba(6, 20, 46, 0.50) 100%),
                url("data:image/png;base64,{base64.b64encode(BACKGROUND_PATH.read_bytes()).decode("ascii") if BACKGROUND_PATH.exists() else ""}");
            background-size: cover;
            background-position: center;
        }}
        .mapa-kpi-wide-tag {{
            position: absolute;
            top: 1rem;
            right: 1.2rem;
            color: #eaf2ff;
            background: rgba(148, 163, 184, 0.20);
            border: 1px solid rgba(184, 208, 255, 0.24);
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
        .raiox-concentration-summary {{
            color: #f8fbff;
            font-size: 1.12rem;
            font-weight: 760;
            line-height: 1.35;
            margin: 0.2rem 0 0.9rem 0;
        }}
        .raiox-concentration-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.7rem;
            margin: 0.2rem 0 1rem 0;
        }}
        .raiox-concentration-pill {{
            border: 1px solid rgba(184, 208, 255, 0.22);
            border-radius: 12px;
            background: rgba(255,255,255,0.07);
            padding: 0.62rem 0.72rem;
        }}
        .raiox-concentration-pill-label {{
            color: #b7c7e6;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        .raiox-concentration-pill-value {{
            color: #ffffff;
            font-size: 1.28rem;
            font-weight: 860;
            margin-top: 0.12rem;
        }}
        .raiox-bar-filter [data-testid="stSelectbox"] {{
            max-width: 16rem;
            margin-left: auto;
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
            .mapa-major-section-title {{
                font-size: 1.55rem;
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


def _empty_map() -> go.Figure:
    fig = go.Figure(
        go.Scattermap(
            lat=[-18.9, -19.92, -21.76],
            lon=[-44.0, -43.94, -43.35],
            mode="markers",
            marker={"size": [18, 26, 14], "color": [32, 65, 44], "colorscale": "Blues", "opacity": 0.65},
            text=["Mapa territorial", "Parquet pendente", "Votos"],
            hoverinfo="text",
        )
    )
    fig.update_layout(
        map={"style": "carto-darkmatter", "center": {"lat": -19.3, "lon": -44.2}, "zoom": 5.2},
        height=520,
        margin={"l": 0, "r": 0, "t": 18, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
    )
    return fig


@st.cache_data(show_spinner=False)
def _load_geo_reference() -> tuple[dict | None, pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    env = load_env()
    bucket_url = env.get("HF_BUCKET_URL", "").rstrip("/")
    if not bucket_url:
        return None, None, None, None

    remote_base = f"{bucket_url}/IBGE/geo-mg"
    fs = hf_filesystem(env.get("HF_TOKEN"))
    geojson_path = f"{remote_base}/geojs-31-mun.json"
    tse_path = f"{remote_base}/municipios_brasileiros_tse.csv"
    municipios_path = f"{remote_base}/municipios.csv"
    regioes_path = f"{remote_base}/municipios.json"

    try:
        with fs.open(geojson_path, "r", encoding="utf-8") as source:
            geojson_mg = json.load(source)
        with fs.open(tse_path, "rb") as source:
            df_tse = pd.read_csv(
                source,
                usecols=["codigo_tse", "uf", "nome_municipio", "codigo_ibge"],
            )
        with fs.open(municipios_path, "rb") as source:
            df_municipios = pd.read_csv(
                source,
                usecols=["codigo_ibge", "nome", "latitude", "longitude"],
            )
    except Exception:
        return None, None, None, None

    df_tse = df_tse[df_tse["uf"].astype(str).str.upper() == "MG"].copy()
    df_tse["codigo_tse"] = pd.to_numeric(df_tse["codigo_tse"], errors="coerce").astype("Int64")
    df_tse["codigo_ibge"] = pd.to_numeric(df_tse["codigo_ibge"], errors="coerce").astype("Int64")
    df_tse["municipio_norm"] = df_tse["nome_municipio"].map(_normalize_municipio_name)

    df_municipios["codigo_ibge"] = pd.to_numeric(
        df_municipios["codigo_ibge"], errors="coerce"
    ).astype("Int64")

    try:
        with fs.open(regioes_path, "r", encoding="utf-8") as source:
            raw_regioes = json.load(source)
        df_regioes = pd.DataFrame(raw_regioes)
        expected = {
            "municipio-id",
            "municipio-nome",
            "mesorregiao-nome",
            "regiao-imediata-nome",
        }
        if expected.issubset(df_regioes.columns):
            df_regioes = df_regioes[
                [
                    "municipio-id",
                    "municipio-nome",
                    "mesorregiao-nome",
                    "regiao-imediata-nome",
                ]
            ].rename(
                columns={
                    "municipio-id": "codigo_ibge",
                    "municipio-nome": "municipio_ibge_nome",
                    "mesorregiao-nome": "mesorregiao_nome",
                    "regiao-imediata-nome": "regiao_imediata_nome",
                }
            )
            df_regioes["codigo_ibge"] = pd.to_numeric(
                df_regioes["codigo_ibge"], errors="coerce"
            ).astype("Int64")
        else:
            df_regioes = pd.DataFrame()
    except Exception:
        df_regioes = pd.DataFrame()

    return geojson_mg, df_tse, df_municipios, df_regioes


def _normalize_municipio_name(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())


def _build_log_colorbar_ticks(max_votes: float) -> tuple[list[float], list[str]]:
    max_v = float(max_votes or 0.0)
    if max_v <= 0:
        return [0.0], ["0"]

    ticks_raw: set[int] = {0}
    scale = 1
    while scale <= max_v:
        for mult in (1, 2, 5):
            candidate = mult * scale
            if candidate <= max_v:
                ticks_raw.add(int(candidate))
        scale *= 10
    ticks_raw.add(int(max_v))

    tickvals = [0.0]
    ticktext = ["0"]
    for raw in sorted(ticks_raw):
        if raw <= 0:
            continue
        tickvals.append(float(np.log10(raw + 1.0)))
        ticktext.append(_format_number(raw))
    return tickvals, ticktext


def _iter_geojson_rings(geometry: dict) -> list[list[list[float]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return coordinates
    if geometry_type == "MultiPolygon":
        return [ring for polygon in coordinates for ring in polygon]
    return []


def _regional_boundary_lines(
    geojson_mg: dict,
    df_regioes_ref: pd.DataFrame | None,
    *,
    include_mesorregiao_boundary: bool,
    include_state_boundary: bool,
) -> tuple[list[float], list[float]]:
    if df_regioes_ref is None or df_regioes_ref.empty:
        return [], []

    regioes = df_regioes_ref[["codigo_ibge", "mesorregiao_nome"]].copy()
    regioes["codigo_ibge_str"] = pd.to_numeric(
        regioes["codigo_ibge"], errors="coerce"
    ).astype("Int64").astype(str).str.zfill(7)
    meso_by_city = dict(zip(regioes["codigo_ibge_str"], regioes["mesorregiao_nome"].astype(str).str.strip()))

    segments: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = {}
    segment_points: dict[tuple[tuple[float, float], tuple[float, float]], tuple[tuple[float, float], tuple[float, float]]] = {}

    for feature in geojson_mg.get("features", []):
        city_id = str(feature.get("properties", {}).get("id", "")).strip().zfill(7)
        mesorregiao = meso_by_city.get(city_id, "")
        if not mesorregiao:
            continue

        for ring in _iter_geojson_rings(feature.get("geometry", {})):
            if len(ring) < 2:
                continue
            for start, end in zip(ring, ring[1:]):
                point_a = (round(float(start[0]), 6), round(float(start[1]), 6))
                point_b = (round(float(end[0]), 6), round(float(end[1]), 6))
                if point_a == point_b:
                    continue
                key = tuple(sorted((point_a, point_b)))
                segments.setdefault(key, []).append(mesorregiao)
                segment_points.setdefault(key, (point_a, point_b))

    lon: list[float] = []
    lat: list[float] = []
    for key, mesorregioes in segments.items():
        is_state_boundary = len(mesorregioes) == 1
        is_mesorregiao_boundary = len(set(mesorregioes)) > 1
        if (include_state_boundary and is_state_boundary) or (
            include_mesorregiao_boundary and is_mesorregiao_boundary
        ):
            point_a, point_b = segment_points[key]
            lon.extend([point_a[0], point_b[0], None])
            lat.extend([point_a[1], point_b[1], None])
    return lon, lat


def _format_number(value: float | int) -> str:
    return f"{float(value):,.0f}".replace(",", ".")


def _format_percent(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "--"
    return f"{float(value) * 100:.1f}%".replace(".", ",")


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
            for file_name in _current_files()
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
    photo_url = _candidate_photo_data_url()
    photo_html = (
        f'<img class="raiox-candidate-photo" src="{photo_url}" alt="Foto do candidato">'
        if photo_url
        else '<div class="raiox-candidate-photo"></div>'
    )
    st.markdown(
        f"""
        <section class="raiox-hero">
            <div class="raiox-hero-title">RAIO X da vota&ccedil;&atilde;o 2022</div>
            <div class="raiox-hero-subtitle">Analises descritivas geograficas e do perfil do eleitor na ultima eleicao.</div>
            <div class="raiox-candidate-row">
                {photo_html}
                <div class="raiox-candidate-info">
                    <div class="raiox-candidate-line">NOME: JOAO VITOR XAVIER</div>
                    <div class="raiox-candidate-line">CARGO: DEPUTADO ESTADUAL</div>
                    <div class="raiox-candidate-line">PARTIDO: CIDADANIA</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


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
        "Mesorregiao": "votos_mesorregiao",
        "Municipio": "votos_municipio",
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
    title = "Top 10 mesorregioes" if kind == "votos_mesorregiao" else "Top 10 municipios"

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
                "colorscale": "Blues",
                "line": {"color": "rgba(255,255,255,0.22)", "width": 0.6},
            },
            customdata=customdata,
            text=trace_text,
            textposition="auto",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Votos: %{customdata[0]:,.0f}<br>Participacao: %{customdata[1]:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        height=560,
        margin={"l": 190, "r": 18, "t": 58, "b": 22},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff", "family": "Segoe UI, Inter, sans-serif"},
        title={"text": title, "x": 0.0, "xanchor": "left", "font": {"size": 18, "color": "#eaf2ff"}},
        xaxis={
            "title": "",
            "showticklabels": False,
            "showgrid": False,
            "range": [0, max_votes * 1.2] if max_votes > 0 else None,
        },
        yaxis={
            "title": "",
            "tickfont": {"size": 11},
            "automargin": True,
            "ticks": "",
        },
        coloraxis_showscale=False,
        bargap=0.32,
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


def _accumulated_concentration_chart(concentration_df: pd.DataFrame) -> go.Figure:
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
        fig.update_layout(height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig

    ref_df = _concentration_reference_rows(concentration_df)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=concentration_df["rank_municipio"],
            y=concentration_df["pct_acumulado"] * 100,
            mode="lines",
            fill="tozeroy",
            line={"color": "#60A5FA", "width": 3},
            fillcolor="rgba(96, 165, 250, 0.20)",
            customdata=np.stack(
                [
                    concentration_df["votos_acumulados"],
                    concentration_df["pct_acumulado"],
                    concentration_df["nm_municipio"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>Top %{x:.0f} munic&iacute;pios</b><br>"
                "%{customdata[0]:,.0f} votos acumulados<br>"
                "%{customdata[1]:.1%} da vota&ccedil;&atilde;o total<br>"
                "Munic&iacute;pio na posi&ccedil;&atilde;o: %{customdata[2]}<extra></extra>"
            ),
            showlegend=False,
        )
    )
    if not ref_df.empty:
        fig.add_trace(
            go.Scatter(
                x=ref_df["rank_municipio"],
                y=ref_df["pct_acumulado"] * 100,
                mode="markers+text",
                marker={"size": 10, "color": "#F8FAFC", "line": {"color": "#60A5FA", "width": 2}},
                text=ref_df["referencia"],
                textposition="top center",
                textfont={"color": "#eaf2ff", "size": 11},
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "%{customdata[0]:,.0f} votos acumulados<br>"
                    "%{customdata[1]:.1%} da vota&ccedil;&atilde;o total<extra></extra>"
                ),
                customdata=np.stack([ref_df["votos_acumulados"], ref_df["pct_acumulado"]], axis=-1),
                showlegend=False,
            )
        )
    fig.update_layout(
        height=430,
        margin={"l": 34, "r": 26, "t": 18, "b": 44},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff", "family": "Segoe UI, Inter, sans-serif"},
        xaxis={
            "title": "Municipios acumulados",
            "gridcolor": "rgba(255,255,255,0.08)",
            "zeroline": False,
        },
        yaxis={
            "title": "% da votacao total",
            "range": [0, 100],
            "ticksuffix": "%",
            "gridcolor": "rgba(255,255,255,0.12)",
            "zeroline": False,
        },
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
        "Concentra&ccedil;&atilde;o Territorial",
        "Quanto da vota&ccedil;&atilde;o total est&aacute; concentrada nos munic&iacute;pios onde o candidato mais recebeu votos.",
    )
    with st.container(border=True):
        if concentration_df.empty:
            st.warning("Nao encontrei dados municipais validos para calcular a concentracao territorial.")
            return

        def pct_at(rank: int) -> float:
            if concentration_df.empty:
                return np.nan
            idx = min(rank, len(concentration_df)) - 1
            return float(concentration_df.iloc[idx]["pct_acumulado"])

        top10_pct = pct_at(10)
        st.markdown(
            f"""
            <div class="raiox-concentration-summary">
                Os 10 principais munic&iacute;pios concentram {_format_percent(top10_pct)} da vota&ccedil;&atilde;o total.
            </div>
            <div class="raiox-concentration-grid">
                <div class="raiox-concentration-pill">
                    <div class="raiox-concentration-pill-label">Top 1</div>
                    <div class="raiox-concentration-pill-value">{_format_percent(pct_at(1))}</div>
                </div>
                <div class="raiox-concentration-pill">
                    <div class="raiox-concentration-pill-label">Top 5</div>
                    <div class="raiox-concentration-pill-value">{_format_percent(pct_at(5))}</div>
                </div>
                <div class="raiox-concentration-pill">
                    <div class="raiox-concentration-pill-label">Top 10</div>
                    <div class="raiox-concentration-pill-value">{_format_percent(top10_pct)}</div>
                </div>
                <div class="raiox-concentration-pill">
                    <div class="raiox-concentration-pill-label">Top 20</div>
                    <div class="raiox-concentration-pill-value">{_format_percent(pct_at(20))}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(_accumulated_concentration_chart(concentration_df), use_container_width=True)


def _render_kpis(df: pd.DataFrame | None) -> None:
    total_votos = "--"
    municipios = "--"
    reduto_nome = "--"
    reduto_votos = "--"
    mesorregiao_nome = "--"
    mesorregiao_votos = "--"

    if df is not None and not df.empty:
        metric_df = df
        if "nivel_territorial" in metric_df.columns:
            municipio_df = metric_df[
                metric_df["nivel_territorial"].astype(str).str.strip().str.lower() == "municipio"
            ].copy()
            if not municipio_df.empty:
                metric_df = municipio_df

        if "qt_votos" in df.columns:
            total_votos = _format_number(pd.to_numeric(metric_df["qt_votos"], errors="coerce").fillna(0).sum())
        if "nm_municipio" in metric_df.columns:
            municipios = _format_number(metric_df["nm_municipio"].dropna().astype(str).str.strip().nunique())
        if {"nm_municipio", "qt_votos"}.issubset(df.columns):
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

    st.markdown(
        f"""
        <div class="mapa-kpi-grid">
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Total de votos</div>
                <div class="mapa-kpi-value">{total_votos}</div>
                <div class="mapa-kpi-caption">Votos nominais no recorte municipal.</div>
            </div>
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Munic&iacute;pio mais votado</div>
                <div class="mapa-kpi-value">{reduto_votos}</div>
                <div class="mapa-kpi-caption">{html.escape(reduto_nome)}</div>
            </div>
            <div class="mapa-kpi-card">
                <div class="mapa-kpi-label">Munic&iacute;pios com votos</div>
                <div class="mapa-kpi-value">{municipios}</div>
                <div class="mapa-kpi-caption">Munic&iacute;pios em que ele foi votado.</div>
            </div>
        </div>
        <div class="mapa-kpi-wide-card">
            <div class="mapa-kpi-wide-tag">Maior concentra&ccedil;&atilde;o</div>
            <div class="mapa-kpi-label">Territ&oacute;rio l&iacute;der</div>
            <div class="mapa-kpi-wide-value">{html.escape(mesorregiao_nome)}</div>
            <div class="mapa-kpi-caption">{mesorregiao_votos} votos</div>
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
    if df is None or df.empty or "qt_votos" not in df.columns:
        return _empty_map()

    if "nivel_territorial" in df.columns:
        municipio_df = df[df["nivel_territorial"].astype(str).str.strip().str.lower() == "municipio"].copy()
        if not municipio_df.empty:
            df = municipio_df

    geojson_mg, df_tse_ref, df_municipios_ref, df_regioes_ref = _load_geo_reference()
    if geojson_mg is None or df_tse_ref is None or df_municipios_ref is None:
        return _empty_map()

    city_col = "nm_municipio" if "nm_municipio" in df.columns else None
    meso_col = "nm_mesorregiao" if "nm_mesorregiao" in df.columns else None
    level_values = (
        df["nivel_territorial"].dropna().astype(str).str.strip().str.lower()
        if "nivel_territorial" in df.columns
        else pd.Series(dtype=str)
    )
    is_mesorregiao_df = bool(meso_col and not level_values.empty and level_values.eq("mesorregiao").all())
    code_col = next(
        (
            col
            for col in (
                "CD_MUNICIPIO",
                "cd_municipio",
                "codigo_tse",
                "codigo_municipio_tse",
                "nr_municipio",
            )
            if col in df.columns
        ),
        None,
    )

    if is_mesorregiao_df and df_regioes_ref is not None and not df_regioes_ref.empty:
        mapa_base = df[[meso_col, "qt_votos"]].copy().rename(columns={meso_col: "mesorregiao_nome"})
        mapa_base["mesorregiao_nome"] = mapa_base["mesorregiao_nome"].astype(str).str.strip()
        mapa_base = mapa_base.groupby("mesorregiao_nome", as_index=False)["qt_votos"].sum()
        mapa_df = df_regioes_ref[["codigo_ibge", "mesorregiao_nome"]].merge(
            mapa_base,
            on="mesorregiao_nome",
            how="left",
        )
        mapa_df = mapa_df.merge(
            df_tse_ref[["codigo_tse", "codigo_ibge", "nome_municipio"]],
            on="codigo_ibge",
            how="left",
        )
        mapa_df["CD_MUNICIPIO"] = mapa_df["codigo_tse"]
        mapa_df["municipio"] = mapa_df["nome_municipio"]
    elif code_col:
        mapa_base = df[[code_col, "qt_votos"] + ([city_col] if city_col else [])].copy()
        rename_cols = {code_col: "CD_MUNICIPIO"}
        if city_col:
            rename_cols[city_col] = "municipio"
        mapa_base = mapa_base.rename(columns=rename_cols)
        mapa_base["CD_MUNICIPIO"] = pd.to_numeric(mapa_base["CD_MUNICIPIO"], errors="coerce").astype("Int64")
        group_cols = ["CD_MUNICIPIO", "municipio"] if "municipio" in mapa_base.columns else ["CD_MUNICIPIO"]
        mapa_base = mapa_base.groupby(group_cols, as_index=False)["qt_votos"].sum()
        mapa_df = mapa_base.merge(
            df_tse_ref[["codigo_tse", "codigo_ibge", "nome_municipio"]],
            left_on="CD_MUNICIPIO",
            right_on="codigo_tse",
            how="left",
        )
        if "municipio" not in mapa_df.columns:
            mapa_df["municipio"] = mapa_df["nome_municipio"]
    elif city_col:
        mapa_base = df[[city_col, "qt_votos"]].copy()
        mapa_base = mapa_base.rename(columns={city_col: "municipio"})
        mapa_base["municipio_norm"] = mapa_base["municipio"].map(_normalize_municipio_name)
        mapa_base = mapa_base.groupby(["municipio_norm", "municipio"], as_index=False)["qt_votos"].sum()
        mapa_df = mapa_base.merge(
            df_tse_ref[["codigo_tse", "codigo_ibge", "nome_municipio", "municipio_norm"]],
            on="municipio_norm",
            how="left",
        )
        mapa_df["CD_MUNICIPIO"] = mapa_df["codigo_tse"]
    else:
        return _empty_map()

    mapa_df["codigo_ibge"] = pd.to_numeric(mapa_df["codigo_ibge"], errors="coerce").astype("Int64")
    mapa_df["codigo_ibge_str"] = mapa_df["codigo_ibge"].astype(str).str.zfill(7)

    geo_ids = []
    for feature in geojson_mg.get("features", []):
        geo_id = str(feature.get("properties", {}).get("id", "")).strip()
        if geo_id:
            geo_ids.append(geo_id.zfill(7))

    malha_df = pd.DataFrame({"codigo_ibge_str": sorted(set(geo_ids))})
    malha_df["codigo_ibge"] = pd.to_numeric(malha_df["codigo_ibge_str"], errors="coerce").astype("Int64")

    mapa_df = malha_df.merge(
        mapa_df[["codigo_ibge_str", "CD_MUNICIPIO", "municipio", "qt_votos", "nome_municipio"]],
        on="codigo_ibge_str",
        how="left",
    )
    mapa_df = mapa_df.merge(df_municipios_ref, on="codigo_ibge", how="left")
    if df_regioes_ref is not None and not df_regioes_ref.empty:
        mapa_df = mapa_df.merge(
            df_regioes_ref[["codigo_ibge", "regiao_imediata_nome", "mesorregiao_nome"]],
            on="codigo_ibge",
            how="left",
        )
    else:
        mapa_df["regiao_imediata_nome"] = ""
        mapa_df["mesorregiao_nome"] = ""

    mapa_df["qt_votos"] = mapa_df["qt_votos"].fillna(0.0).astype(float)
    mapa_df["votos_color"] = np.where(mapa_df["qt_votos"] > 0, np.log10(mapa_df["qt_votos"] + 1.0), 0.0)
    mapa_df["CD_MUNICIPIO"] = mapa_df["CD_MUNICIPIO"].fillna(0).astype(int)
    mapa_df["municipio_exibicao"] = (
        mapa_df["nome"].fillna(mapa_df["nome_municipio"]).fillna(mapa_df["municipio"]).fillna("Municipio sem voto")
    )

    max_votes = float(mapa_df["qt_votos"].max()) if not mapa_df.empty else 0.0
    zmax = float(np.log10(max_votes + 1.0)) if max_votes > 0 else 1.0
    tickvals, ticktext = _build_log_colorbar_ticks(max_votes)
    map_title = (
        "ConcentraÃ§Ã£o de Votos por <b>mesorregiÃ£o</b> (MG)"
        if is_mesorregiao_df
        else "ConcentraÃ§Ã£o de votos por municÃ­pio (MG)"
    )

    fig = px.choropleth(
        mapa_df,
        geojson=geojson_mg,
        locations="codigo_ibge_str",
        featureidkey="properties.id",
        color="votos_color",
        hover_name="municipio_exibicao",
        hover_data={
            "votos_color": False,
            "CD_MUNICIPIO": True,
            "mesorregiao_nome": True,
            "regiao_imediata_nome": True,
            "latitude": ":.4f",
            "longitude": ":.4f",
            "codigo_ibge_str": False,
        },
        custom_data=["CD_MUNICIPIO", "latitude", "longitude", "qt_votos"],
        color_continuous_scale=[
            [0.00, "#FFFFFF"],
            [0.000001, "#E8F1FF"],
            [0.16, "#BFD9FF"],
            [0.42, "#60A5FA"],
            [0.70, "#2563EB"],
            [1.00, "#0B1F4D"],
        ],
        title=map_title,
        template=st.session_state.get("theme", "plotly_white"),
        range_color=[0.0, zmax],
    )
    fig.update_traces(
        marker_line_color="rgba(210,228,255,0)" if is_mesorregiao_df else "rgba(210,228,255,0.75)",
        marker_line_width=0.15 if is_mesorregiao_df else 0.7,
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "<span style='color:#93c5fd'>Votos:</span> %{customdata[3]:,.0f}<br>"
            "<span style='color:#93c5fd'>CÃ³d. municÃ­pio (TSE):</span> %{customdata[0]}<br>"
            "<span style='color:#93c5fd'>Lat/Lon:</span> %{customdata[1]:.4f}, %{customdata[2]:.4f}<extra></extra>"
        ),
        hoverlabel={
            "bgcolor": "rgba(5,12,28,0.95)",
            "font_color": "#EAF2FF",
            "font_size": 12,
            "bordercolor": "rgba(147,197,253,0.55)",
        },
    )
    if is_mesorregiao_df:
        boundary_lon, boundary_lat = _regional_boundary_lines(
            geojson_mg,
            df_regioes_ref,
            include_mesorregiao_boundary=True,
            include_state_boundary=False,
        )
        if boundary_lon and boundary_lat:
            fig.add_trace(
                go.Scattergeo(
                    lon=boundary_lon,
                    lat=boundary_lat,
                    mode="lines",
                    line={"color": "rgba(255,255,255,0.92)", "width": 2.4},
                    hoverinfo="skip",
                    showlegend=False,
                    name="Fronteiras das mesorregioes",
                )
            )
        state_lon, state_lat = _regional_boundary_lines(
            geojson_mg,
            df_regioes_ref,
            include_mesorregiao_boundary=False,
            include_state_boundary=True,
        )
        if state_lon and state_lat:
            fig.add_trace(
                go.Scattergeo(
                    lon=state_lon,
                    lat=state_lat,
                    mode="lines",
                    line={"color": "rgba(255,255,255,0.98)", "width": 3.4},
                    hoverinfo="skip",
                    showlegend=False,
                    name="Limite de Minas Gerais",
                )
            )
        label_df = (
            mapa_df[["mesorregiao_nome", "qt_votos", "latitude", "longitude"]]
            .dropna(subset=["mesorregiao_nome", "latitude", "longitude"])
            .assign(mesorregiao_nome=lambda frame: frame["mesorregiao_nome"].astype(str).str.strip())
        )
        label_df = label_df[label_df["mesorregiao_nome"].ne("")]
        if not label_df.empty:
            label_df = (
                label_df.groupby("mesorregiao_nome", as_index=False)
                .agg({"qt_votos": "first", "latitude": "mean", "longitude": "mean"})
            )
            total_meso_votes = float(pd.to_numeric(label_df["qt_votos"], errors="coerce").fillna(0).sum())
            if total_meso_votes > 0:
                label_df["pct_votos"] = (
                    pd.to_numeric(label_df["qt_votos"], errors="coerce").fillna(0)
                    / total_meso_votes
                )
                label_df = label_df[label_df["pct_votos"] > 0]
                fig.add_trace(
                    go.Scattergeo(
                        lon=label_df["longitude"],
                        lat=label_df["latitude"],
                        mode="text",
                        text=label_df["pct_votos"].map(_format_percent),
                        textfont={"color": "#ffffff", "size": 13, "family": "Segoe UI, Inter, sans-serif"},
                        hoverinfo="skip",
                        showlegend=False,
                        name="Participacao da mesorregiao",
                    )
                )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        margin={"l": 6, "r": 36, "t": 52, "b": 6},
        height=560,
        coloraxis_colorbar={
            "title": {"text": "Votos", "font": {"color": "#eaf2ff"}},
            "tickvals": tickvals,
            "ticktext": ticktext,
            "len": 0.8,
            "thickness": 13,
            "xpad": 8,
            "x": 1.02,
            "xanchor": "left",
            "tickfont": {"color": "#b7c7e6"},
        },
        paper_bgcolor="rgba(255,255,255,0.0)",
        plot_bgcolor="rgba(255,255,255,0.0)",
        font={"color": "#eaf2ff", "family": "Segoe UI, Inter, sans-serif"},
        title={"font": {"size": 20, "color": "#eaf2ff"}},
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

    code_cols = [col for col in ("cd_municipio", "cd_bairro") if col in tree_df.columns]
    agg_map = {"qt_votos": "sum", **{col: "first" for col in code_cols}}
    tree_df = (
        tree_df.groupby(group_cols, as_index=False)
        .agg(agg_map)
        .sort_values("qt_votos", ascending=False)
        .head(500)
    )
    if tree_df.empty:
        return _empty_treemap("Votacao territorial"), pd.DataFrame()

    fig = px.treemap(tree_df, path=group_cols, values="qt_votos")
    code_lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in tree_df.to_dict("records"):
        municipio = str(row.get("nm_municipio") or "")
        bairro = str(row.get("nm_bairro") or "")
        code_lookup[(municipio, bairro)] = {
            col: str(row.get(col) or "")
            for col in code_cols
        }

    customdata = []
    ids = []
    for trace_id, label, parent in zip(fig.data[0].ids, fig.data[0].labels, fig.data[0].parents):
        parts = str(trace_id).split("/")
        municipio = parts[0] if parts else ""
        bairro = parts[1] if len(parts) > 1 else ""
        codes = code_lookup.get((municipio, bairro), {})
        ids.append(str(trace_id))
        customdata.append(
            [
                municipio,
                bairro,
                codes.get("cd_municipio", ""),
                codes.get("cd_bairro", ""),
                str(label),
                str(parent),
            ]
        )
    fig.update_traces(
        ids=ids,
        customdata=customdata,
        hovertemplate="<b>%{label}</b><br>Votos: %{value:,.0f}<extra></extra>",
    )
    fig.update_layout(
        height=500,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
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
        height=500,
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
        customdata = point.get("customdata")
        label = str(point.get("label") or "")
        parent = str(point.get("parent") or "")
    else:
        customdata = getattr(point, "customdata", None)
        label = str(getattr(point, "label", "") or "")
        parent = str(getattr(point, "parent", "") or "")
    if customdata is None:
        customdata = []
    if len(customdata) >= 4:
        municipio = str(customdata[0] or "")
        bairro = str(customdata[1] or "")
        cd_municipio = str(customdata[2] or "")
        cd_bairro = str(customdata[3] or "")
    else:
        municipio = parent or label
        bairro = "" if not parent else label
        cd_municipio = ""
        cd_bairro = ""

    selection: dict[str, str] = {}
    if cd_municipio:
        selection["cd_municipio"] = cd_municipio
    if cd_bairro:
        selection["cd_bairro"] = cd_bairro
    if municipio:
        selection["nm_municipio"] = municipio
    if bairro:
        selection["nm_bairro"] = bairro
    return selection


def _apply_territorial_context(df: pd.DataFrame, context: dict[str, str], mesorregiao: str) -> pd.DataFrame:
    result = df.copy()
    if mesorregiao != "Todas" and "nm_mesorregiao" in result.columns:
        result = result[result["nm_mesorregiao"].astype(str).str.strip() == mesorregiao]
    for column in ("cd_municipio", "cd_bairro", "nm_municipio", "nm_bairro"):
        value = context.get(column)
        if column in result.columns and value:
            result = result[result[column].astype(str).str.strip() == value]
    return result


def _demographic_bar(kind: str, context: dict[str, str], mesorregiao: str) -> go.Figure:
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
        df = _apply_territorial_context(df, context, mesorregiao)
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


_apply_visual_model()

_render_page_header()

_major_section_header("Mapa Territorial da Vota&ccedil;&atilde;o", "Leitura territorial do desempenho eleitoral no recorte ativo.")
votos_municipio_df = _read_selected_parquet("votos_municipio")
votos_bairro_df = _read_selected_parquet("votos_bairro")
_render_kpis(votos_municipio_df)
header_col, filter_col = st.columns([0.72, 0.28], gap="large")
with header_col:
    _section_header(
        "Sua vota&ccedil;&atilde;o no territ&oacute;rio de Minas Gerais",
        "Concentra&ccedil;&atilde;o territorial dos votos por Messoregi&atilde;o e por Municipio.",
    )
with filter_col:
    territorial_kind = _territorial_kind_select()
votos_df = _territorial_map_view(_read_selected_parquet(territorial_kind), territorial_kind)
map_col, concentration_col = st.columns([0.68, 0.32], gap="large")
with map_col:
    st.plotly_chart(_territorial_map(votos_df), use_container_width=True)
with concentration_col:
    with st.container(border=True):
        st.markdown(
            "<div class='raiox-chart-card-title'>Concentra&ccedil;&atilde;o territorial</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _territorial_concentration_chart(votos_df, territorial_kind),
            use_container_width=True,
        )
_section_header(
    "Vota&ccedil;&atilde;o por Bairro de cada munic&iacute;pio e Perfil demogr&aacute;fico",
    "Treemap territorial e distribuicao demografica conforme parquet selecionado.",
)
treemap_df, mesorregiao = _mesorregiao_filter(votos_bairro_df)
col_left, col_right = st.columns(2, gap="large")
with col_left:
    with st.container(border=True):
        st.markdown(
            "<div class='raiox-chart-card-title'>Votacao por Municipio e Bairro</div>",
            unsafe_allow_html=True,
        )
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
    with st.container(border=True):
        st.markdown(
            "<div class='raiox-bar-title'>Distribui&ccedil;&atilde;o por perfil demogr&aacute;fico</div>",
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
        st.plotly_chart(_demographic_bar(perfil_kind, territorial_context, mesorregiao), use_container_width=True)
        if territorial_context:
            label = territorial_context.get("nm_bairro") or territorial_context.get("nm_municipio")
            st.caption(f"Recorte do treemap: {label}")

_render_accumulated_concentration_section(votos_municipio_df)


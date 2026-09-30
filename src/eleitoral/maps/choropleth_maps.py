"""Plotly choropleths built from the IBGE GeoParquets on Hugging Face."""

from __future__ import annotations

import unicodedata

import numpy as np
import pandas as pd
import plotly.express as px
from shapely.geometry import mapping

from eleitoral.maps.dna_geo_reference import load_geo_layer, load_geo_reference, load_municipality_sectors


def _style(fig, *, colorbar_title: str = ""):
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)")
    fig.update_traces(marker_line_color="rgba(210,228,255,0.75)", marker_line_width=0.45)
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 4, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
        coloraxis_colorbar={"title": colorbar_title},
    )
    return fig


def continuous_choropleth(
    frame: pd.DataFrame, geojson: dict, *, location: str, color: str,
    colors: list[str], hover_name: str, custom_data: list[str] | None = None,
    colorbar_title: str = "", color_range: tuple[float, float] | None = None,
):
    fig = px.choropleth(
        frame, geojson=geojson, locations=location, featureidkey="properties.id",
        color=color, hover_name=hover_name, custom_data=custom_data,
        color_continuous_scale=colors, range_color=color_range,
    )
    return _style(fig, colorbar_title=colorbar_title)


def categorical_choropleth(
    frame: pd.DataFrame, geojson: dict, *, location: str, category: str,
    categories: list[str], colors: list[str], hover_name: str,
    custom_data: list[str] | None = None,
):
    plot_frame = frame.copy()
    plot_frame["_category_index"] = plot_frame[category].map({value: index for index, value in enumerate(categories)})
    count = len(categories)
    scale = [stop for index, color in enumerate(colors)
             for stop in ((index / count, color), ((index + 1) / count, color))]
    fig = continuous_choropleth(
        plot_frame, geojson, location=location, color="_category_index",
        colors=scale, hover_name=hover_name, custom_data=custom_data,
        color_range=(-0.5, count - 0.5),
    )
    fig.update_coloraxes(colorbar={"tickvals": list(range(count)), "ticktext": categories, "title": ""})
    return fig


def territorial_map(votes: pd.DataFrame | None, kind: str):
    geojson, tse, municipalities, regions = load_geo_reference()
    if not geojson or votes is None or votes.empty:
        return None
    if kind == "votos_mesorregiao":
        totals = votes.groupby("nm_mesorregiao")["qt_votos"].sum()
        frame = regions[["codigo_ibge", "mesorregiao_nome"]].copy()
        frame["votos"] = frame["mesorregiao_nome"].map(totals).fillna(0)
    else:
        frame = votes.copy()
        if "nivel_territorial" in frame.columns:
            rows = frame["nivel_territorial"].astype(str).str.lower().eq("municipio")
            if rows.any():
                frame = frame[rows]
        if "cd_ibge_municipio" in frame.columns:
            frame["codigo_ibge"] = pd.to_numeric(frame["cd_ibge_municipio"], errors="coerce")
        else:
            code_col = next((col for col in ("cd_municipio", "CD_MUNICIPIO", "codigo_tse") if col in frame), None)
            if code_col is None:
                return None
            frame["codigo_tse"] = pd.to_numeric(frame[code_col], errors="coerce")
            frame = frame.merge(tse[["codigo_tse", "codigo_ibge"]], on="codigo_tse", how="left")
        frame = frame.groupby("codigo_ibge", as_index=False)["qt_votos"].sum().rename(columns={"qt_votos": "votos"})
    frame["codigo_ibge"] = pd.to_numeric(frame["codigo_ibge"], errors="coerce").astype("Int64")
    frame = frame.dropna(subset=["codigo_ibge"])
    frame = frame.groupby("codigo_ibge", as_index=False)["votos"].sum()
    all_cities = municipalities[["codigo_ibge", "nome"]].drop_duplicates("codigo_ibge")
    frame = all_cities.merge(frame, on="codigo_ibge", how="left")
    frame["votos"] = pd.to_numeric(frame["votos"], errors="coerce").fillna(0)
    frame["codigo_ibge_str"] = frame["codigo_ibge"].astype(str).str.zfill(7)
    frame["votos_cor"] = np.log1p(frame["votos"])
    fig = continuous_choropleth(
        frame, geojson, location="codigo_ibge_str", color="votos_cor",
        colors=["#e8f1ff", "#bfd9ff", "#60a5fa", "#2563eb", "#0b1f4d"],
        hover_name="nome", custom_data=["votos"], colorbar_title="Votos",
    )
    fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>Votos: %{customdata[0]:,.0f}<extra></extra>")
    return fig


ACTION_COLORS = {
    "Reduto Atendido": "#2563EB", "Investimento": "#16A34A",
    "Reduto Desassistido": "#FACC15", "Sem Expressão": "#F97316",
    "Votos sem emendas": "#64748B", "Sem votos nem emendas": "#FFFFFF",
}


def parliamentary_map(action: pd.DataFrame):
    geojson, _, municipalities, _ = load_geo_reference()
    if not geojson or action is None or action.empty:
        return None
    frame = municipalities[["codigo_ibge", "nome"]].drop_duplicates("codigo_ibge").rename(columns={"nome": "nome_malha"})
    frame["codigo_ibge_str"] = frame["codigo_ibge"].astype(str).str.zfill(7)
    action = action.copy()
    action["codigo_ibge_str"] = action["codigo_ibge_str"].astype(str).str.zfill(7)
    frame = frame.merge(action, on="codigo_ibge_str", how="left")
    frame["categoria_coerencia"] = frame["categoria_coerencia"].fillna("Sem votos nem emendas")
    frame["municipio_exibicao"] = frame["municipio_exibicao"].fillna(frame["nome_malha"])
    frame["qt_votos"] = pd.to_numeric(frame["qt_votos"], errors="coerce").fillna(0)
    frame["valor_emendas"] = pd.to_numeric(frame["valor_emendas"], errors="coerce").fillna(0)
    fig = categorical_choropleth(
        frame, geojson, location="codigo_ibge_str", category="categoria_coerencia",
        categories=list(ACTION_COLORS), colors=list(ACTION_COLORS.values()),
        hover_name="municipio_exibicao", custom_data=["categoria_coerencia", "qt_votos", "valor_emendas"],
    )
    fig.update_traces(hovertemplate=(
        "<b>%{hovertext}</b><br>%{customdata[0]}<br>Votos: %{customdata[1]:,.0f}"
        "<br>Emendas: R$ %{customdata[2]:,.2f}<extra></extra>"
    ))
    return fig


def _normalized_name(value: object) -> str:
    name = unicodedata.normalize("NFKD", str(value or "").strip().upper())
    return " ".join("".join(char for char in name if not unicodedata.combining(char)).split())


def _code(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().removesuffix(".0")


def detailed_map(votes: pd.DataFrame, municipality_code: int):
    votes = votes.copy()
    votes["qt_votos"] = pd.to_numeric(votes.get("qt_votos"), errors="coerce").fillna(0)
    bairros = load_geo_layer("bairro")
    bairros = bairros[pd.to_numeric(bairros["code_muni"], errors="coerce").eq(municipality_code)]
    if not bairros.empty:
        geometry, source, id_col = bairros.drop_duplicates("code_neighborhood"), "bairros oficiais do IBGE", "code_neighborhood"
        names = votes.groupby(votes["nm_bairro"].map(_normalized_name))["qt_votos"].sum() if "nm_bairro" in votes else pd.Series(dtype=float)
        vote_labels = (
            votes.dropna(subset=["nm_bairro"]).groupby(votes["nm_bairro"].map(_normalized_name))["nm_bairro"].first()
            if "nm_bairro" in votes else pd.Series(dtype=str)
        )
        geometry = geometry.copy()
        geometry["votos"] = geometry["name_neighborhood"].map(_normalized_name).map(names).fillna(0)
        geometry["nome"] = geometry["name_neighborhood"].astype(str)
        geometry["context_key"] = "nm_bairro"
        geometry["context_value"] = geometry["name_neighborhood"].map(_normalized_name).map(vote_labels).fillna("")
    else:
        areas = load_geo_layer("area_ponderada")
        areas = areas[pd.to_numeric(areas["code_muni"], errors="coerce").eq(municipality_code)]
        if len(areas) > 5:
            geometry, source, id_col = areas.drop_duplicates("code_weighting"), "áreas ponderadas do IBGE", "code_weighting"
            geometry = geometry.copy()
            geometry["votos"] = 0.0
            geometry["nome"] = geometry["name_weighting"].astype(str)
            geometry["context_key"] = ""
            geometry["context_value"] = ""
        else:
            geometry, source, id_col = load_municipality_sectors(municipality_code).drop_duplicates("code_tract"), "setores censitários do IBGE", "code_tract"
            geometry = geometry.copy()
            sector_votes = votes.groupby(votes["cd_setor_censitario"].map(_code))["qt_votos"].sum() if "cd_setor_censitario" in votes else pd.Series(dtype=float)
            geometry["votos"] = geometry["code_tract"].map(_code).map(sector_votes).fillna(0)
            geometry["nome"] = "Setor " + geometry["code_tract"].map(_code)
            geometry["context_key"] = "cd_setor_censitario"
            geometry["context_value"] = geometry["code_tract"].map(_code)
    if geometry.empty:
        return None, "Malha territorial indisponível para este município."
    geometry = geometry[geometry["geometry"].notna()].copy()
    geometry["id"] = "territorio-" + geometry[id_col].map(_code)
    features = [{
        "type": "Feature", "properties": {"id": row.id},
        "geometry": mapping(row.geometry.simplify(0.0001, preserve_topology=True)),
    } for row in geometry.itertuples(index=False)]
    geojson = {"type": "FeatureCollection", "features": features}
    geometry["votos_cor"] = np.log1p(geometry["votos"])
    max_color = max(1.0, float(geometry["votos_cor"].max()))
    fig = continuous_choropleth(
        geometry, geojson, location="id", color="votos_cor",
        colors=["#9fbfe5", "#154d9c"], hover_name="nome",
        custom_data=["votos", "context_key", "context_value", "nome"],
        colorbar_title="Votos", color_range=(0.0, max_color),
    )
    fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>Votos associados: %{customdata[0]:,.0f}<extra></extra>")
    note = f"Malha: {source}. Votos e legenda: bairros eleitorais de stage01b_bairros."
    return fig, note


def selected_context(event: object) -> dict[str, str]:
    selection = event.get("selection", {}) if isinstance(event, dict) else getattr(event, "selection", {})
    points = selection.get("points", []) if isinstance(selection, dict) else getattr(selection, "points", [])
    if not points:
        return {}
    data = points[0].get("customdata", [])
    if len(data) < 4 or not data[1] or not data[2]:
        return {}
    return {str(data[1]): str(data[2]), "nome_bairro": str(data[3])}

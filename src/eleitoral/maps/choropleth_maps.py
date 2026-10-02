"""Plotly choropleths built from the IBGE GeoParquets on Hugging Face."""

from __future__ import annotations

import unicodedata

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from eleitoral.maps.dna_geo_reference import load_geo_reference


def _normalized_name(value: object) -> str:
    name = unicodedata.normalize("NFKD", str(value or "").strip().upper())
    return " ".join("".join(char for char in name if not unicodedata.combining(char)).split())


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


def _add_boundary(fig, coordinates: tuple[list, list], *, width: float) -> None:
    lon, lat = coordinates
    if lon and lat:
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat, mode="lines",
            line={"color": "rgba(255,255,255,0.96)", "width": width},
            hoverinfo="skip", showlegend=False,
        ))


def territorial_map(votes: pd.DataFrame | None, kind: str):
    geojson, tse, municipalities, _ = load_geo_reference()
    if not geojson or votes is None or votes.empty:
        return None
    if kind == "votos_mesorregiao":
        totals = votes.groupby(votes["nm_mesorregiao"].map(_normalized_name))["qt_votos"].sum()
        mesoregion_geojson = geojson.get("mesoregions", {})
        features = mesoregion_geojson.get("features", [])
        if not features:
            return None
        frame = pd.DataFrame({"nome": [feature["properties"]["id"] for feature in features]})
        frame["votos"] = frame["nome"].map(_normalized_name).map(totals).fillna(0)
        frame["votos"] = pd.to_numeric(frame["votos"], errors="coerce").fillna(0)
        frame["votos_cor"] = np.log1p(frame["votos"])
        fig = continuous_choropleth(
            frame, mesoregion_geojson, location="nome", color="votos_cor",
            colors=["#e8f1ff", "#bfd9ff", "#60a5fa", "#2563eb", "#0b1f4d"],
            hover_name="nome", custom_data=["votos"], colorbar_title="Votos",
        )
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
    boundaries = geojson.get("regional_lines", {})
    if kind == "votos_mesorregiao":
        fig.update_traces(marker_line_color="rgba(255,255,255,0.96)", marker_line_width=1.5)
        centers = geojson.get("mesoregion_centers", [])
        total_votes = float(pd.to_numeric(votes["qt_votos"], errors="coerce").fillna(0).sum())
        labels = []
        custom_data = []
        for center in centers:
            region_votes = float(totals.get(_normalized_name(center["name"]), 0))
            percentage = 100 * region_votes / total_votes if total_votes > 0 else 0.0
            labels.append(f"{percentage:.1f}%".replace(".", ","))
            custom_data.append([center["name"], region_votes])
        if centers:
            fig.add_trace(go.Scattergeo(
                lon=[center["lon"] for center in centers],
                lat=[center["lat"] for center in centers],
                mode="markers+text", text=labels, textposition="middle center",
                textfont={"color": "#FFFFFF", "size": 11, "family": "Arial Black, Arial, sans-serif"},
                marker={
                    "size": 46, "color": "rgba(5,18,43,0.86)",
                    "line": {"color": "#FFFFFF", "width": 1.2},
                },
                customdata=custom_data,
                hovertemplate="<b>%{customdata[0]}</b><br>Participação: %{text}<br>Votos: %{customdata[1]:,.0f}<extra></extra>",
                showlegend=False,
            ))
    else:
        fig.update_traces(marker_line_color="rgba(255,255,255,0.92)", marker_line_width=1.0)
    _add_boundary(fig, boundaries.get("state", ([], [])), width=3.0)
    return fig


ACTION_COLORS = {
    "Reduto Atendido": "#2563EB", "Investimento": "#16A34A",
    "Reduto Desassistido": "#FACC15", "Sem Expressão": "#F97316",
    "Votos sem emendas": "#64748B", "Sem votos nem emendas": "#FFFFFF",
}

ACTION_LEGEND = {
    "Reduto Atendido": "Reduto eleitoral com emendas",
    "Investimento": "Emendas destinadas ao município",
    "Reduto Desassistido": "Reduto com retorno limitado",
    "Sem Expressão": "Baixa expressão eleitoral",
    "Votos sem emendas": "Recebeu votos, sem emendas",
    "Sem votos nem emendas": "Sem votos e sem emendas",
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
        hover_name="municipio_exibicao", custom_data=["categoria_coerencia", "qt_votos", "valor_emendas", "codigo_ibge_str"],
    )
    fig.update_traces(hovertemplate=(
        "<b>%{hovertext}</b><br>%{customdata[0]}<br>Votos: %{customdata[1]:,.0f}"
        "<br>Emendas: R$ %{customdata[2]:,.2f}<extra></extra>"
    ))
    fig.update_geos(domain={"x": [0, 0.72], "y": [0, 1]})
    fig.update_coloraxes(colorbar={
        "title": {"text": "Leitura das cores", "side": "top", "font": {"size": 13, "color": "#f8fbff"}},
        "tickvals": list(range(len(ACTION_COLORS))),
        "ticktext": [
            f"<b>{name}</b><br><span style='color:#b7c7e6'>{ACTION_LEGEND[name]}</span>"
            for name in ACTION_COLORS
        ],
        "tickfont": {"size": 11, "color": "#eaf2ff"},
        "ticklen": 0,
        "thickness": 20,
        "len": 0.86,
        "x": 0.76,
        "xanchor": "left",
        "y": 0.5,
        "outlinecolor": "rgba(177,211,255,0.35)",
        "outlinewidth": 1,
    })
    return fig

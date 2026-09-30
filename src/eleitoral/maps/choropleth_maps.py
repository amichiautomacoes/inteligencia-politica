"""Plotly choropleths built from the IBGE GeoParquets on Hugging Face."""

from __future__ import annotations

import html
import unicodedata

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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


def _normalized_name(value: object) -> str:
    name = unicodedata.normalize("NFKD", str(value or "").strip().upper())
    return " ".join("".join(char for char in name if not unicodedata.combining(char)).split())


def _code(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().removesuffix(".0")


def _fallback_vote_groups(votes: pd.DataFrame, code_column: str) -> pd.DataFrame:
    """Aggregate candidate votes and neighborhood names by IBGE polygon code."""
    if code_column not in votes:
        return pd.DataFrame(columns=["votos", "bairros", "bairros_hover"])
    rows = votes.copy()
    rows["_geo_code"] = rows[code_column].map(_code)
    rows = rows[rows["_geo_code"].ne("")]
    if rows.empty:
        return pd.DataFrame(columns=["votos", "bairros", "bairros_hover"])

    def names(values: pd.Series) -> list[str]:
        unique = {str(value).strip() for value in values.dropna() if str(value).strip()}
        return sorted(unique, key=_normalized_name)

    grouped = rows.groupby("_geo_code").agg(
        votos=("qt_votos", "sum"),
        names=("nm_bairro", names),
    )
    grouped["bairros"] = grouped["names"].map(lambda values: ", ".join(values) or "Não informado")
    bairro_votes = (
        rows.assign(_bairro=rows["nm_bairro"].fillna("Não informado").astype(str).str.strip())
        .groupby(["_geo_code", "_bairro"], as_index=False)["qt_votos"]
        .sum()
    )
    bairro_votes["_hover_line"] = bairro_votes.apply(
        lambda row: f"{html.escape(row['_bairro'])}: {row['qt_votos']:,.0f}".replace(",", "."), axis=1
    )
    grouped["bairros_hover"] = bairro_votes.groupby("_geo_code")["_hover_line"].agg("<br>".join)
    return grouped.drop(columns="names")


def _bind_fallback_votes(geometry: pd.DataFrame, votes: pd.DataFrame, *, shape_code: str, vote_code: str) -> tuple[pd.DataFrame, float]:
    geometry = geometry.copy()
    geometry["_geo_code"] = geometry[shape_code].map(_code)
    grouped = _fallback_vote_groups(votes, vote_code)
    geometry["votos"] = geometry["_geo_code"].map(grouped["votos"]).fillna(0.0)
    geometry["bairros"] = geometry["_geo_code"].map(grouped["bairros"]).fillna("Sem bairro eleitoral associado")
    geometry["bairros_hover"] = geometry["_geo_code"].map(grouped["bairros_hover"]).fillna("Sem bairro eleitoral associado")
    matched_votes = float(grouped.loc[grouped.index.isin(geometry["_geo_code"]), "votos"].sum())
    return geometry, matched_votes


def detailed_map(votes: pd.DataFrame, municipality_code: int):
    votes = votes.copy()
    votes["qt_votos"] = pd.to_numeric(votes.get("qt_votos"), errors="coerce").fillna(0)
    bairros = load_geo_layer("bairro")
    bairros = bairros[pd.to_numeric(bairros["code_muni"], errors="coerce").eq(municipality_code)]
    if not bairros.empty:
        source_kind = "bairro"
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
        area_codes = set(areas["code_weighting"].map(_code)) if not areas.empty else set()
        vote_area_codes = set(votes["cd_area_ponderada"].map(_code)) if "cd_area_ponderada" in votes else set()
        if len(areas) > 5 and area_codes.intersection(vote_area_codes):
            source_kind = "area_ponderada"
            geometry, source, id_col = areas.drop_duplicates("code_weighting"), "áreas ponderadas do IBGE", "code_weighting"
            geometry, matched_votes = _bind_fallback_votes(
                geometry, votes, shape_code=id_col, vote_code="cd_area_ponderada"
            )
            geometry["nome"] = "Área ponderada " + geometry["_geo_code"]
            geometry["context_key"] = "cd_area_ponderada"
            geometry["context_value"] = geometry["_geo_code"]
        else:
            source_kind = "setor"
            geometry, source, id_col = load_municipality_sectors(municipality_code).drop_duplicates("code_tract"), "setores censitários do IBGE", "code_tract"
            geometry, matched_votes = _bind_fallback_votes(
                geometry, votes, shape_code=id_col, vote_code="cd_setor_censitario"
            )
            geometry["nome"] = "Setor " + geometry["_geo_code"]
            geometry["context_key"] = "cd_setor_censitario"
            geometry["context_value"] = geometry["_geo_code"]
    if geometry.empty:
        return None, "Malha territorial indisponível para este município."
    geometry = geometry[geometry["geometry"].notna()].copy()
    if geometry.empty:
        return None, "Malha territorial indisponível para este município."
    geometry["id"] = "territorio-" + geometry[id_col].map(_code)
    features = [{
        "type": "Feature", "properties": {"id": row.id},
        "geometry": mapping(row.geometry.simplify(0.0001, preserve_topology=True)),
    } for row in geometry.itertuples(index=False)]
    geojson = {"type": "FeatureCollection", "features": features}
    geometry["votos_cor"] = np.log1p(geometry["votos"])
    max_color = max(1.0, float(geometry["votos_cor"].max()))
    custom_data = ["votos", "context_key", "context_value", "nome"]
    if source_kind != "bairro":
        custom_data += ["bairros", "bairros_hover"]
    fig = continuous_choropleth(
        geometry, geojson, location="id", color="votos_cor",
        colors=["#9fbfe5", "#154d9c"], hover_name="nome",
        custom_data=custom_data,
        colorbar_title="Votos", color_range=(0.0, max_color),
    )
    if source_kind == "bairro":
        fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>Votos associados: %{customdata[0]:,.0f}<extra></extra>")
    else:
        fig.update_traces(hovertemplate=(
            "<b>%{hovertext}</b><br>Votos associados: %{customdata[0]:,.0f}"
            "<br>Bairros eleitorais:<br>%{customdata[5]}<extra></extra>"
        ))
        maximum = float(geometry["votos"].max())
        ticks = np.unique(np.rint(np.linspace(0, maximum, 5)).astype(int))
        fig.update_coloraxes(colorbar={
            "title": "Votos", "tickvals": np.log1p(ticks).tolist(),
            "ticktext": [f"{value:,.0f}".replace(",", ".") for value in ticks],
        })
    note = f"Malha: {source}. Votos e legenda: bairros eleitorais de stage01b_bairros."
    if source_kind != "bairro":
        unmatched = max(0, round(float(votes["qt_votos"].sum()) - matched_votes))
        if unmatched:
            note += f" {unmatched:,} votos sem correspondência com esta malha.".replace(",", ".")
    return fig, note


def selected_context(event: object) -> dict[str, str]:
    selection = event.get("selection", {}) if isinstance(event, dict) else getattr(event, "selection", {})
    points = selection.get("points", []) if isinstance(selection, dict) else getattr(selection, "points", [])
    if not points:
        return {}
    data = points[0].get("customdata", [])
    if len(data) < 4 or not data[1] or not data[2]:
        return {}
    context = {str(data[1]): str(data[2]), "nome_bairro": str(data[3])}
    if len(data) > 4 and data[4] and data[4] != "Sem bairro eleitoral associado":
        context["bairros"] = str(data[4])
    return context

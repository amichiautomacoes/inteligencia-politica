"""Municipal geometry with electoral neighborhood votes for Raio X."""

from __future__ import annotations

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import mapping

from eleitoral.maps.dna_geo_reference import load_geo_layer, load_municipality_sectors


def municipality_options() -> list[tuple[int, str]]:
    municipalities = load_geo_layer("municipio")
    rows = municipalities[["code_muni", "name_muni"]].dropna().drop_duplicates("code_muni")
    return sorted(
        ((int(row.code_muni), str(row.name_muni)) for row in rows.itertuples(index=False)),
        key=lambda item: item[1].casefold(),
    )


def municipality_mesh(municipality_code: int) -> tuple[str, pd.DataFrame, str, str]:
    """Select geometry by availability, without joining electoral data."""
    neighborhoods = load_geo_layer("bairro")
    neighborhoods = neighborhoods.loc[
        pd.to_numeric(neighborhoods["code_muni"], errors="coerce").eq(municipality_code)
    ]
    if not neighborhoods.empty:
        return "bairro", neighborhoods, "code_neighborhood", "name_neighborhood"

    areas = load_geo_layer("area_ponderada")
    areas = areas.loc[pd.to_numeric(areas["code_muni"], errors="coerce").eq(municipality_code)]
    if areas["code_weighting"].dropna().nunique() > 8:
        return "area_ponderada", areas, "code_weighting", "code_weighting"

    sectors = load_municipality_sectors(municipality_code)
    return "setor", sectors, "code_tract", "code_tract"


def _code(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().removesuffix(".0")


def municipality_mesh_map(
    municipality_code: int, votes: pd.DataFrame | None,
) -> tuple[go.Figure | None, int]:
    kind, mesh, code_column, _ = municipality_mesh(municipality_code)
    mesh = mesh.dropna(subset=[code_column, "geometry"]).copy()
    mesh = mesh.loc[mesh["geometry"].map(lambda shape: not shape.is_empty)]
    mesh["id"] = mesh[code_column].map(_code)
    mesh = mesh.loc[mesh["id"].ne("")].drop_duplicates("id")
    if mesh.empty:
        return None, 0

    vote_code = {
        "bairro": "cd_ibge_bairro",
        "area_ponderada": "cd_area_ponderada",
        "setor": "cd_setor_censitario",
    }[kind]
    required = {"cd_ibge_municipio", vote_code, "nm_bairro", "qt_votos"}
    if votes is None or not required.issubset(votes.columns):
        return None, 0
    rows = votes.loc[votes["cd_ibge_municipio"].map(_code).eq(str(municipality_code))].copy()
    rows["_code"] = rows[vote_code].map(_code)
    rows["_name"] = rows["nm_bairro"].fillna("").astype(str).str.strip()
    rows["qt_votos"] = pd.to_numeric(rows["qt_votos"], errors="coerce").fillna(0)
    rows = rows.loc[rows["_code"].ne("")]
    by_neighborhood = rows.groupby(["_code", "_name"], as_index=False)["qt_votos"].sum()
    by_neighborhood["_name"] = by_neighborhood["_name"].replace("", "Bairro não informado")
    by_neighborhood = by_neighborhood.groupby(["_code", "_name"], as_index=False)["qt_votos"].sum()
    totals = by_neighborhood.groupby("_code")["qt_votos"].sum()
    details = by_neighborhood.groupby("_code").apply(
        lambda group: "<br>".join(
            f"{html.escape(str(name))}: {int(count):,} votos".replace(",", ".")
            for name, count in zip(group.sort_values("_name")["_name"], group.sort_values("_name")["qt_votos"])
        ),
        include_groups=False,
    ) if not by_neighborhood.empty else pd.Series(dtype=str)

    mesh["votes"] = mesh["id"].map(totals).fillna(0)
    matched_rows = rows.loc[rows["_code"].isin(mesh["id"]), "qt_votos"].sum()
    if not np.isclose(mesh["votes"].sum(), matched_rows):
        raise ValueError("A soma dos votos na malha diverge dos registros eleitorais associados.")
    mesh["details"] = mesh["id"].map(details).fillna("Sem votos associados")
    mesh["total_label"] = mesh["votes"].map(lambda value: f"{int(value):,}".replace(",", "."))
    active_share = float(mesh["votes"].gt(0).mean())
    max_votes = float(mesh["votes"].max())
    mesh["color_intensity"] = (
        np.log1p(mesh["votes"]) / np.log1p(max_votes) * np.sqrt(active_share)
        if max_votes > 0 else 0.0
    )
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": row.id},
                "geometry": mapping(row.geometry.simplify(0.0001, preserve_topology=True)),
            }
            for row in mesh.itertuples(index=False)
        ],
    }
    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=mesh["id"],
        z=mesh["color_intensity"],
        zmin=0,
        zmax=1,
        featureidkey="properties.id",
        colorscale=[
            [0, "#e8f1ff"], [0.25, "#bfd9ff"], [0.5, "#60a5fa"],
            [0.75, "#2563eb"], [1, "#0b1f4d"],
        ],
        showscale=False,
        marker_line_color="rgba(225,238,255,0.8)",
        marker_line_width=0.65,
        customdata=mesh[["total_label", "details"]],
        hovertemplate="<b>Total de votos: %{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
    ))
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
    )
    return fig, len(mesh)

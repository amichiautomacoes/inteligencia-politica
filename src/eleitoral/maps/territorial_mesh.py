"""Municipal geometry with electoral neighborhood votes for Raio X."""

from __future__ import annotations

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import Point, mapping

from eleitoral.maps.dna_geo_reference import (
    load_geo_layer,
    load_geo_reference,
    load_municipality_sectors,
    load_sector_neighborhood_lookup,
)


def mesoregion_options() -> list[str]:
    """Return the official Minas Gerais mesoregions used by the filters."""
    _, _, _, regions = load_geo_reference()
    if regions is None or regions.empty or "mesorregiao_nome" not in regions.columns:
        return []
    return sorted(
        {
            str(value).strip()
            for value in regions["mesorregiao_nome"].dropna()
            if str(value).strip()
        },
        key=str.casefold,
    )


def municipality_options(mesorregiao: str | None = None) -> list[tuple[str, str]]:
    municipalities = load_geo_layer("municipio")
    rows = municipalities[["code_muni", "name_muni"]].dropna().drop_duplicates("code_muni")
    if mesorregiao and mesorregiao != "Todas":
        _, _, _, regions = load_geo_reference()
        if regions is not None and not regions.empty and {
            "codigo_ibge", "mesorregiao_nome"
        }.issubset(regions.columns):
            selected_codes = regions.loc[
                regions["mesorregiao_nome"].astype(str).str.strip().eq(mesorregiao),
                "codigo_ibge",
            ].astype("string")
            rows = rows.loc[rows["code_muni"].astype("string").isin(selected_codes)]
    return sorted(
        ((str(row.code_muni), str(row.name_muni)) for row in rows.itertuples(index=False)),
        key=lambda item: item[1].casefold(),
    )


def municipality_mesh(municipality_code: str) -> tuple[str, pd.DataFrame, str, str]:
    """Select geometry by availability, without joining electoral data."""
    neighborhoods = load_geo_layer("bairro")
    neighborhoods = neighborhoods.loc[
        neighborhoods["code_muni"].astype("string").eq(str(municipality_code))
    ]
    if not neighborhoods.empty:
        return "bairro", neighborhoods, "code_neighborhood", "name_neighborhood"

    areas = load_geo_layer("area_ponderada")
    areas = areas.loc[areas["code_muni"].astype("string").eq(str(municipality_code))]
    if areas["code_weighting"].dropna().nunique() > 8:
        return "area_ponderada", areas, "code_weighting", "code_weighting"

    sectors = load_municipality_sectors(municipality_code)
    return "setor", sectors, "code_tract", "code_tract"


def _attach_coordinate_matches(rows: pd.DataFrame, mesh: pd.DataFrame) -> pd.DataFrame:
    """Associate rows without a territorial code using their polling coordinates.

    ``stage01b_bairros`` contains a few electoral rows aggregated by bairro where
    the census-sector code is empty or does not belong to the selected mesh.  A
    strict code-only join silently drops those votes.  Coordinates are the only
    non-invented fallback available in that situation, so assign each row to the
    polygon that contains its polling point (or the nearest polygon when a point
    lies exactly on a boundary).
    """
    if rows.empty or not {"nr_latitude", "nr_longitude"}.issubset(rows.columns):
        return rows

    unmatched = rows[rows["_code"].eq("") | ~rows["_code"].isin(mesh["id"])].copy()
    if unmatched.empty:
        return rows

    lat = pd.to_numeric(unmatched["nr_latitude"], errors="coerce")
    lon = pd.to_numeric(unmatched["nr_longitude"], errors="coerce")
    valid = lat.between(-23.5, -14.0) & lon.between(-52.5, -39.0)
    if not valid.any():
        return rows

    geometries = list(mesh["geometry"])
    ids = list(mesh["id"])
    for index in unmatched.index[valid]:
        point = Point(float(lon.loc[index]), float(lat.loc[index]))
        containing = [position for position, geometry in enumerate(geometries) if geometry.covers(point)]
        if containing:
            rows.loc[index, "_code"] = ids[containing[0]]
            continue
        # A polling point can be a few metres outside a simplified polygon.
        nearest = min(range(len(geometries)), key=lambda position: geometries[position].distance(point))
        if geometries[nearest].distance(point) <= 0.002:
            rows.loc[index, "_code"] = ids[nearest]
    return rows


def municipality_mesh_map(
    municipality_code: str, votes: pd.DataFrame | None,
) -> tuple[go.Figure | None, int]:
    kind, mesh, code_column, label_column = municipality_mesh(municipality_code)
    mesh = mesh.dropna(subset=[code_column, "geometry"]).copy()
    mesh = mesh.loc[mesh["geometry"].map(lambda shape: not shape.is_empty)]
    mesh["id"] = mesh[code_column].astype("string")
    mesh = mesh.loc[mesh["id"].notna() & mesh["id"].ne("")].drop_duplicates("id")
    if mesh.empty:
        return None, 0

    # Official neighborhood geometry carries its own name. The compact sector
    # geometry does not, so recover the corresponding IBGE neighborhood names
    # from the lightweight sector lookup when it is available.
    mesh["_mesh_name"] = ""
    if label_column in mesh.columns and label_column != code_column:
        mesh["_mesh_name"] = mesh[label_column].fillna("").astype(str).str.strip()
    if kind == "setor":
        try:
            lookup = load_sector_neighborhood_lookup()
            if {"cd_setor_censitario", "nome_bairro_ibge"}.issubset(lookup.columns):
                lookup = lookup.copy()
                lookup["_code"] = lookup["cd_setor_censitario"].astype("string")
                lookup["_name"] = lookup["nome_bairro_ibge"].fillna("").astype(str).str.strip()
                lookup = lookup.loc[lookup["_code"].ne("") & lookup["_name"].ne("")]
                names = lookup.groupby("_code")["_name"].apply(
                    lambda values: " / ".join(dict.fromkeys(values))
                )
                mesh["_mesh_name"] = mesh["id"].map(names).fillna(mesh["_mesh_name"])
        except Exception:
            # The map remains usable if the optional reference table is absent.
            pass

    vote_code = {
        "bairro": "cd_ibge_bairro",
        "area_ponderada": "cd_area_ponderada",
        "setor": "cd_setor_censitario",
    }[kind]
    required = {"cd_ibge_municipio", vote_code, "nm_bairro", "qt_votos"}
    if votes is None or not required.issubset(votes.columns):
        return None, 0
    rows = votes.loc[votes["cd_ibge_municipio"].astype("string").eq(str(municipality_code))].copy()
    rows["_code"] = rows[vote_code].astype("string")
    rows["_name"] = rows["nm_bairro"].fillna("").astype(str).str.strip()
    rows["qt_votos"] = pd.to_numeric(rows["qt_votos"], errors="coerce").fillna(0)
    rows = _attach_coordinate_matches(rows, mesh)
    rows = rows.loc[rows["_code"].notna() & rows["_code"].ne("")]
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
    mesh["details"] = mesh["id"].map(details).fillna("")
    mesh["details"] = mesh.apply(
        lambda row: row["details"]
        if row["details"]
        else (
            f"{html.escape(row['_mesh_name'])}: 0 votos"
            if row["_mesh_name"] else "Sem votos associados"
        ),
        axis=1,
    )
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

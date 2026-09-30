"""Municipal voting map: official neighborhoods with census-sector fallback."""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from pages.deck_maps import deck_geojson, ramp, zoom_for_bounds
from pages.dna_geo_reference import load_geo_layer, load_municipality_sectors, load_sector_neighborhood_lookup


def _name(value: object) -> str:
    if pd.isna(value):
        return ""
    value = unicodedata.normalize("NFKD", str(value).upper())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", " ", value).strip()


def assign_vote_polygons(votes: pd.DataFrame, neighborhoods: pd.DataFrame) -> pd.DataFrame:
    """Assign each electoral row to an IBGE neighborhood, if supported by its sector or name."""
    result = votes.copy()
    result["codigo_bairro_ibge"] = pd.NA
    if result.empty or neighborhoods.empty:
        return result
    sector_codes = load_sector_neighborhood_lookup()
    result = result.merge(sector_codes, on="cd_setor_censitario", how="left", suffixes=("", "_setor"))
    result["codigo_bairro_ibge"] = result["codigo_bairro_ibge_setor"].where(
        result["codigo_bairro_ibge_setor"].isin(neighborhoods["codigo_bairro_ibge"])
    )
    result = result.drop(columns="codigo_bairro_ibge_setor")
    names = neighborhoods[["codigo_bairro_ibge", "bairro"]].copy()
    names["name_key"] = names["bairro"].map(_name)
    names = names[~names.duplicated("name_key", keep=False)].set_index("name_key")["codigo_bairro_ibge"]
    electoral_name = result["cd_bairro"].fillna("").str.extract(r"_BAIRRO:(.*)$", expand=False).fillna(result["nm_bairro"])
    missing = result["codigo_bairro_ibge"].isna()
    result.loc[missing, "codigo_bairro_ibge"] = electoral_name.loc[missing].map(_name).map(names)
    return result


def detailed_map(votes: pd.DataFrame, municipality_code: int):
    municipality = load_geo_layer("municipio")
    municipality = municipality[pd.to_numeric(municipality["code_muni"], errors="coerce").eq(municipality_code)]
    if municipality.empty:
        return None, "Município ausente da malha do IBGE."
    bounds = tuple(municipality.iloc[0].geometry.bounds)
    official = load_geo_layer("bairro_geopedia")
    official = official[official["codigo_municipio_ibge"].eq(str(municipality_code))].copy()
    votes = votes.copy()
    votes["qt_votos"] = pd.to_numeric(votes["qt_votos"], errors="coerce").fillna(0)
    features = []
    note = ""
    if not official.empty:
        assigned = assign_vote_polygons(votes, official)
        by_bairro = assigned.groupby("codigo_bairro_ibge", dropna=True)["qt_votos"].sum()
        max_votes = max(1.0, float(by_bairro.max()) if not by_bairro.empty else 1.0)
        for row in official.itertuples(index=False):
            total = float(by_bairro.get(row.codigo_bairro_ibge, 0))
            features.append({"type": "Feature", "geometry": row.geometry.simplify(0.00015, preserve_topology=True).__geo_interface__,
                "properties": {"id": "bairro-" + row.codigo_bairro_ibge, "codigo_bairro_ibge": row.codigo_bairro_ibge,
                    "nome": row.bairro, "votos": int(total), "fonte": "Bairro IBGE",
                    "fill_color": ramp(np.sqrt(total / max_votes), ["#f5f9ff", "#b7d3f4", "#4d8fd7"])}})
        remaining = assigned[assigned["codigo_bairro_ibge"].isna()]
        note = "Malha: bairros oficiais; setores censitários nos votos sem bairro correspondente."
    else:
        remaining = votes
        note = "Malha: setores censitários do IBGE (sem bairros oficiais disponíveis)."

    # Only load the large sector geometry when the municipality needs a fallback.
    if not remaining.empty:
        sectors = load_municipality_sectors(municipality_code).copy()
        sectors["cd_setor_censitario"] = pd.to_numeric(sectors["code_tract"], errors="coerce").astype("Int64").astype(str)
        sectors = sectors.drop_duplicates("cd_setor_censitario")
        remaining = remaining.copy()
        remaining["cd_setor_censitario"] = remaining["cd_setor_censitario"].fillna("").astype(str)
        by_sector = remaining.groupby("cd_setor_censitario")["qt_votos"].sum()
        max_votes = max(1.0, float(by_sector.max()) if not by_sector.empty else 1.0)
        # In a municipality without official neighborhoods, show every sector.
        if not official.empty:
            sectors = sectors[sectors["cd_setor_censitario"].isin(by_sector.index)]
        for row in sectors.itertuples(index=False):
            total = float(by_sector.get(row.cd_setor_censitario, 0))
            features.append({"type": "Feature", "geometry": row.geometry.simplify(0.00015, preserve_topology=True).__geo_interface__,
                "properties": {"id": "setor-" + row.cd_setor_censitario, "cd_setor_censitario": row.cd_setor_censitario,
                    "nome": "Setor " + row.cd_setor_censitario, "votos": int(total), "fonte": "Setor censitário",
                    "fill_color": ramp(np.sqrt(total / max_votes), ["#f5f9ff", "#b7d3f4", "#4d8fd7"])}})
        unmapped = remaining.loc[~remaining["cd_setor_censitario"].isin(sectors["cd_setor_censitario"]), "qt_votos"].sum()
        if unmapped:
            note += f" {int(unmapped):,} votos sem polígono correspondente."

    return deck_geojson(
        features, layer_id="bairros-setores", pickable=True,
        latitude=(bounds[1] + bounds[3]) / 2, longitude=(bounds[0] + bounds[2]) / 2,
        zoom=zoom_for_bounds(bounds),
        tooltip="<b>{nome}</b><br/>Votos associados: {votos}<br/>{fonte}",
    ), note


def selected_context(event: object) -> dict[str, str]:
    selection = event.get("selection", {}) if isinstance(event, dict) else getattr(event, "selection", {})
    objects = selection.get("objects", {}) if isinstance(selection, dict) else getattr(selection, "objects", {})
    selected = (objects.get("bairros-setores") or []) if isinstance(objects, dict) else []
    if not selected:
        return {}
    props = selected[0].get("properties", selected[0])
    if props.get("codigo_bairro_ibge"):
        return {"codigo_bairro_ibge": str(props["codigo_bairro_ibge"])}
    if props.get("cd_setor_censitario"):
        return {"cd_setor_censitario": str(props["cd_setor_censitario"])}
    return {}

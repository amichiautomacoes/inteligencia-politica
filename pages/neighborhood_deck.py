"""Municipal voting map using IBGE census sectors."""

from __future__ import annotations

import html
import numpy as np
import pandas as pd

from pages.deck_maps import deck_geojson, ramp, zoom_for_bounds
from pages.dna_geo_reference import load_geo_layer, load_municipality_sectors, load_sector_neighborhood_lookup


def _sector_code(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").astype("Int64").astype(str)


def detailed_map(votes: pd.DataFrame, municipality_code: int):
    municipality = load_geo_layer("municipio")
    municipality = municipality[pd.to_numeric(municipality["code_muni"], errors="coerce").eq(municipality_code)]
    if municipality.empty:
        return None, "Município ausente da malha do IBGE."

    bounds = tuple(municipality.iloc[0].geometry.bounds)
    sectors = load_municipality_sectors(municipality_code).copy()
    if sectors.empty:
        return None, "Setores censitários indisponíveis para este município."
    sectors["cd_setor_censitario"] = _sector_code(sectors["code_tract"])
    sectors = sectors.drop_duplicates("cd_setor_censitario")

    votes = votes.copy()
    votes["cd_setor_censitario"] = _sector_code(votes["cd_setor_censitario"])
    votes["qt_votos"] = pd.to_numeric(votes["qt_votos"], errors="coerce").fillna(0)
    by_sector = votes.groupby("cd_setor_censitario")["qt_votos"].sum()
    mapped_votes = by_sector.reindex(sectors["cd_setor_censitario"], fill_value=0)
    max_votes = max(1.0, float(mapped_votes.max()) if not mapped_votes.empty else 1.0)

    lookup = load_sector_neighborhood_lookup().copy()
    lookup["cd_setor_censitario"] = _sector_code(lookup["cd_setor_censitario"])
    lookup = lookup[lookup["cd_setor_censitario"].isin(sectors["cd_setor_censitario"])]
    names = {}
    if "nome_bairro_ibge" in lookup.columns:
        lookup["nome_bairro_ibge"] = lookup["nome_bairro_ibge"].fillna("").astype(str).str.strip()
        names = (lookup[lookup["nome_bairro_ibge"].ne("")]
                 .groupby("cd_setor_censitario")["nome_bairro_ibge"]
                 .agg(lambda values: ", ".join(sorted(set(str(value).strip() for value in values if str(value).strip()))))
                 .to_dict())
    if "nm_bairro" in votes.columns:
        electoral_names = (votes.assign(nm_bairro=votes["nm_bairro"].fillna("").astype(str).str.strip())
                           .loc[lambda frame: frame["nm_bairro"].ne("")]
                           .groupby("cd_setor_censitario")["nm_bairro"]
                           .agg(lambda values: ", ".join(sorted(set(values))))
                           .to_dict())
        for code, electoral_name in electoral_names.items():
            if code in names:
                combined = {part.strip() for part in (names[code] + ", " + electoral_name).split(",") if part.strip()}
                names[code] = ", ".join(sorted(combined))
            else:
                names[code] = electoral_name

    features = []
    for row in sectors.itertuples(index=False):
        code = row.cd_setor_censitario
        total = float(by_sector.get(code, 0))
        features.append({
            "type": "Feature",
            "geometry": row.geometry.__geo_interface__,
            "properties": {
                "id": "setor-" + code,
                "cd_setor_censitario": code,
                "nome": html.escape(names.get(code) or "Bairro não informado"),
                "votos": int(total),
                "fill_color": ramp(np.sqrt(total / max_votes), ["#9fbfe5", "#5a91cd", "#154d9c"]),
            },
        })
    unmapped = votes.loc[~votes["cd_setor_censitario"].isin(sectors["cd_setor_censitario"]), "qt_votos"].sum()
    note = "Malha: setores censitários do IBGE. Azul relativo à votação dos setores deste município."
    if unmapped:
        note += f" {int(unmapped):,} votos sem setor correspondente."
    return deck_geojson(
        features, layer_id="bairros-setores", pickable=True,
        latitude=(bounds[1] + bounds[3]) / 2, longitude=(bounds[0] + bounds[2]) / 2,
        zoom=zoom_for_bounds(bounds),
        line_width=2, line_color=[255, 255, 255, 235],
        tooltip="<b>{nome}</b><br/>Votos associados: {votos}<br/>Setor censitário do IBGE",
    ), note


def selected_context(event: object) -> dict[str, str]:
    selection = event.get("selection", {}) if isinstance(event, dict) else getattr(event, "selection", {})
    objects = selection.get("objects", {}) if isinstance(selection, dict) else getattr(selection, "objects", {})
    selected = (objects.get("bairros-setores") or []) if isinstance(objects, dict) else []
    if not selected:
        return {}
    props = selected[0].get("properties", selected[0])
    if props.get("cd_setor_censitario"):
        return {"cd_setor_censitario": str(props["cd_setor_censitario"]), "nome_bairro": html.unescape(str(props.get("nome", "")))}
    return {}

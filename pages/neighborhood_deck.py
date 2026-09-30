"""Adaptive IBGE territorial detail map."""
from __future__ import annotations
import html
import pandas as pd
from pages.deck_maps import deck_geojson, ramp, zoom_for_bounds
from pages.dna_geo_reference import load_geo_layer, load_municipality_sectors

def detailed_map(votes: pd.DataFrame, municipality_code: int):
    votes = votes.copy()
    votes["qt_votos"] = pd.to_numeric(votes.get("qt_votos"), errors="coerce").fillna(0)
    total = int(votes["qt_votos"].sum())
    names = sorted({str(v).strip() for v in votes.get("nm_bairro", pd.Series(dtype=str)).dropna() if str(v).strip()})
    label = ", ".join(names[:8]) or "Bairro não informado"
    if len(names) > 8: label += f" (+{len(names)-8})"
    bairros = load_geo_layer("bairro")
    bairros = bairros[pd.to_numeric(bairros["code_muni"], errors="coerce").eq(municipality_code)]
    if not bairros.empty:
        geometry, source, id_col = bairros.drop_duplicates("code_neighborhood"), "bairros oficiais do IBGE", "code_neighborhood"
    else:
        areas = load_geo_layer("area_ponderada")
        areas = areas[pd.to_numeric(areas["code_muni"], errors="coerce").eq(municipality_code)]
        if len(areas) > 5:
            geometry, source, id_col = areas.drop_duplicates("code_weighting"), "áreas ponderadas do IBGE", "code_weighting"
        else:
            geometry, source, id_col = load_municipality_sectors(municipality_code).drop_duplicates("code_tract"), "setores censitários do IBGE", "code_tract"
    if geometry.empty: return None, "Malha territorial indisponível para este município."
    features = []
    for row in geometry.itertuples(index=False):
        features.append({"type":"Feature", "geometry":row.geometry.__geo_interface__, "properties": {"id":"territorio-"+str(getattr(row,id_col)), "nome":html.escape(label), "votos":total, "fill_color":ramp(1.0 if total else 0.0,["#9fbfe5","#154d9c"])}})
    bounds = tuple(geometry.total_bounds)
    return deck_geojson(features, layer_id="bairros-setores", pickable=True, latitude=(bounds[1]+bounds[3])/2, longitude=(bounds[0]+bounds[2])/2, zoom=zoom_for_bounds(bounds), line_width=2, line_color=[255,255,255,235], tooltip="<b>{nome}</b><br/>Votos associados: {votos}<br/>Fonte territorial: IBGE"), f"Malha: {source}. Votos e legenda: bairros eleitorais de stage01b_bairros."

def selected_context(event: object) -> dict[str, str]:
    selection = event.get("selection", {}) if isinstance(event, dict) else getattr(event, "selection", {})
    objects = selection.get("objects", {}) if isinstance(selection, dict) else getattr(selection, "objects", {})
    selected = (objects.get("bairros-setores") or []) if isinstance(objects, dict) else []
    if not selected: return {}
    props = selected[0].get("properties", selected[0])
    return {"nome_bairro": html.unescape(str(props.get("nome", "")))} if props.get("nome") else {}

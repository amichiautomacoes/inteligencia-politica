"""Deck.gl versions of the municipal maps."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pages.deck_maps import deck_geojson, municipality_features, ramp, rgb
from pages.dna_geo_reference import load_geo_reference


def territorial_deck(votes: pd.DataFrame | None, kind: str):
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
        frame = frame.groupby("codigo_ibge", as_index=False)["qt_votos"].sum()
        frame = frame.rename(columns={"qt_votos": "votos"})
    frame["codigo_ibge"] = pd.to_numeric(frame["codigo_ibge"], errors="coerce").astype("Int64").astype(str)
    frame["votos"] = pd.to_numeric(frame["votos"], errors="coerce").fillna(0)
    frame = frame.groupby("codigo_ibge", as_index=False)["votos"].sum()
    max_votes = max(1.0, float(frame["votos"].max()) if not frame.empty else 1.0)
    values = {}
    for row in frame.itertuples(index=False):
        values[row.codigo_ibge] = {
            "votos": int(row.votos),
            "fill_color": ramp(np.log1p(row.votos) / np.log1p(max_votes),
                               ["#e8f1ff", "#bfd9ff", "#60a5fa", "#2563eb", "#0b1f4d"]),
        }
    features = municipality_features(geojson, values)
    names = dict(zip(municipalities["codigo_ibge"].astype(str), municipalities["nome"].astype(str)))
    for feature in features:
        feature["properties"].setdefault("votos", 0)
        feature["properties"]["nome"] = names.get(feature["properties"]["id"], "Município")
    return deck_geojson(features, layer_id="votos-municipios", tooltip="<b>{nome}</b><br/>Votos: {votos}")


ACTION_COLORS = {
    "Reduto Atendido": "#2563EB", "Investimento": "#16A34A",
    "Reduto Desassistido": "#FACC15", "Sem Expressão": "#F97316",
    "Votos sem emendas": "#64748B", "Sem votos nem emendas": "#FFFFFF",
}


def parliamentary_deck(action: pd.DataFrame):
    geojson, _, _, _ = load_geo_reference()
    if not geojson or action is None or action.empty:
        return None
    values = {}
    for row in action.itertuples(index=False):
        code = str(row.codigo_ibge_str).zfill(7)
        category = row.categoria_coerencia
        values[code] = {
            "nome": str(row.municipio_exibicao), "categoria": category,
            "votos": int(row.qt_votos), "emendas": f"R$ {row.valor_emendas:,.2f}",
            "motivo": str(row.motivo_cor),
            "fill_color": rgb(ACTION_COLORS.get(category, "#FFFFFF")),
        }
    features = municipality_features(geojson, values)
    for feature in features:
        feature["properties"].setdefault("nome", feature["properties"]["id"])
        feature["properties"].setdefault("categoria", "Sem votos nem emendas")
        feature["properties"].setdefault("votos", 0)
        feature["properties"].setdefault("emendas", "R$ 0")
        feature["properties"].setdefault("motivo", "")
    return deck_geojson(features, layer_id="atuacao-parlamentar",
        tooltip="<b>{nome}</b><br/>{categoria}<br/>Votos: {votos}<br/>Emendas: {emendas}<br/>{motivo}")

import unicodedata

import pandas as pd
import streamlit as st
from shapely import wkb
from shapely.geometry import mapping

from hf_sync import hf_filesystem, load_env


@st.cache_data(show_spinner=False)
def load_geo_reference() -> tuple[dict | None, pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    env = load_env()
    bucket_url = env.get("HF_BUCKET_URL", "").rstrip("/")
    if not bucket_url:
        return None, None, None, None

    remote_base = f"{bucket_url}/IBGE/MG/dadosterritorio"
    fs = hf_filesystem(env.get("HF_TOKEN"))
    try:
        with fs.open(f"{remote_base}/MG_municipios_2022.parquet", "rb") as source:
            municipalities = pd.read_parquet(source, columns=["code_muni", "name_muni", "geometry"])
        with fs.open(f"{remote_base}/municipios_mg_mesorregioes.parquet", "rb") as source:
            reference = pd.read_parquet(source)
    except Exception:
        return None, None, None, None

    municipalities["codigo_ibge"] = pd.to_numeric(municipalities["code_muni"], errors="coerce").astype("Int64")
    municipalities = municipalities.dropna(subset=["codigo_ibge", "geometry"])
    features = []
    coordinates = []
    for row in municipalities.itertuples(index=False):
        geometry = wkb.loads(row.geometry)
        municipality_id = str(int(row.codigo_ibge))
        features.append({
            "type": "Feature",
            "properties": {"id": municipality_id},
            "geometry": mapping(geometry),
        })
        point = geometry.representative_point()
        coordinates.append((int(row.codigo_ibge), row.name_muni, point.y, point.x))
    geojson_mg = {"type": "FeatureCollection", "features": features}

    df_municipios = pd.DataFrame(coordinates, columns=["codigo_ibge", "nome", "latitude", "longitude"])
    df_municipios["codigo_ibge"] = df_municipios["codigo_ibge"].astype("Int64")

    reference["codigo_ibge"] = pd.to_numeric(reference["codigo_ibge"], errors="coerce").astype("Int64")
    reference["codigo_tse"] = pd.to_numeric(reference["codigo_tse"], errors="coerce").astype("Int64")
    df_tse = reference[["codigo_tse", "codigo_ibge", "nm_municipio_ibge"]].rename(
        columns={"nm_municipio_ibge": "nome_municipio"}
    ).copy()
    df_tse["municipio_norm"] = df_tse["nome_municipio"].map(normalize_municipio_name)

    df_regioes = reference[["codigo_ibge", "nm_municipio_ibge", "nm_mesorregiao"]].rename(
        columns={"nm_municipio_ibge": "municipio_ibge_nome", "nm_mesorregiao": "mesorregiao_nome"}
    ).copy()
    df_regioes["regiao_imediata_nome"] = ""
    return geojson_mg, df_tse, df_municipios, df_regioes


def normalize_municipio_name(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())

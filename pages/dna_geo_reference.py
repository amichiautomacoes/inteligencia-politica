import unicodedata

import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import mapping
from shapely.ops import unary_union

from hf_sync import hf_filesystem, load_env


GEOGRAPHY_FILES = {
    "municipio": "MG_municipios_2022.parquet",
    "mesorregiao": "MG_mesorregioes_2022.parquet",
    "area_ponderada": "MG_AreaPonderada_CD2022.parquet",
    "bairro": "MG_bairros_CD2022.parquet",
    "setor": "MG_setores_CD2022.parquet",
    "bairro_geopedia": "malha_bairros_completa.parquet",
}


@st.cache_data(show_spinner=False)
def load_sector_neighborhood_lookup() -> pd.DataFrame:
    """Read the compact sector-to-neighborhood index, without geometries."""
    env = load_env()
    path = env["HF_BUCKET_URL"].rstrip("/") + "/IBGE/MG/dadosterritorio/setor_bairro_lookup.parquet"
    with hf_filesystem(env.get("HF_TOKEN")).open(path, "rb") as source:
        return pd.read_parquet(source)


@st.cache_data(show_spinner=False)
def load_municipality_sectors(municipality_code: int) -> gpd.GeoDataFrame:
    """Read one municipality from the compact, row-grouped sector map."""
    env = load_env()
    path = env["HF_BUCKET_URL"].rstrip("/") + "/IBGE/MG/dadosterritorio/MG_setores_mapa_CD2022.parquet"
    with hf_filesystem(env.get("HF_TOKEN")).open(path, "rb") as source:
        layer = gpd.read_parquet(source, filters=[("code_muni", "==", int(municipality_code))])
    return layer.to_crs("EPSG:4326")


@st.cache_data(show_spinner=False)
def load_geo_layer(granularity: str) -> gpd.GeoDataFrame:
    """Read an official IBGE GeoParquet layer, preserving its CRS and geometry."""
    if granularity not in GEOGRAPHY_FILES:
        raise ValueError(f"Granularidade geográfica desconhecida: {granularity}")
    env = load_env()
    bucket_url = env.get("HF_BUCKET_URL", "").rstrip("/")
    if not bucket_url:
        raise RuntimeError("HF_BUCKET_URL não foi configurado.")
    path = f"{bucket_url}/IBGE/MG/dadosterritorio/{GEOGRAPHY_FILES[granularity]}"
    with hf_filesystem(env.get("HF_TOKEN")).open(path, "rb") as source:
        layer = gpd.read_parquet(source)
    if layer.crs is None:
        raise ValueError(f"A malha {path} não informa o sistema de coordenadas.")
    return layer.to_crs("EPSG:4326")


@st.cache_data(show_spinner=False)
def load_geo_reference() -> tuple[dict | None, pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    env = load_env()
    bucket_url = env.get("HF_BUCKET_URL", "").rstrip("/")
    if not bucket_url:
        return None, None, None, None

    fs = hf_filesystem(env.get("HF_TOKEN"))
    try:
        municipalities = load_geo_layer("municipio")[["code_muni", "name_muni", "geometry"]]
        mesoregions = load_geo_layer("mesorregiao")[["geometry"]]
        with fs.open(f"{bucket_url}/IBGE/MG/dadosterritorio/municipios_mg_mesorregioes.parquet", "rb") as source:
            reference = pd.read_parquet(source)
    except Exception as exc:
        st.warning(f"Não foi possível carregar a malha municipal de MG: {exc}")
        return None, None, None, None

    municipalities["codigo_ibge"] = pd.to_numeric(municipalities["code_muni"], errors="coerce").astype("Int64")
    municipalities = municipalities.dropna(subset=["codigo_ibge", "geometry"])
    features = []
    coordinates = []
    for row in municipalities.itertuples(index=False):
        geometry = row.geometry
        municipality_id = str(int(row.codigo_ibge))
        features.append({
            "type": "Feature",
            "properties": {"id": municipality_id},
            "geometry": mapping(geometry.simplify(0.005, preserve_topology=True)),
        })
        point = geometry.representative_point()
        coordinates.append((int(row.codigo_ibge), row.name_muni, point.y, point.x))
    region_geometries = list(mesoregions.geometry.dropna())
    geojson_mg = {
        "type": "FeatureCollection",
        "features": features,
        "regional_lines": {
            "mesoregions": _boundary_coordinates([geometry.boundary for geometry in region_geometries]),
            "state": _boundary_coordinates([unary_union(region_geometries).boundary]),
        },
    }

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


def _boundary_coordinates(boundaries: list) -> tuple[list[float | None], list[float | None]]:
    lon: list[float | None] = []
    lat: list[float | None] = []
    for boundary in boundaries:
        simplified = boundary.simplify(0.002, preserve_topology=True)
        parts = simplified.geoms if hasattr(simplified, "geoms") else [simplified]
        for part in parts:
            for x, y in part.coords:
                lon.append(float(x))
                lat.append(float(y))
            lon.append(None)
            lat.append(None)
    return lon, lat

from __future__ import annotations

import json
import unicodedata

import pandas as pd
import streamlit as st

from hf_sync import hf_filesystem, load_env


@st.cache_data(show_spinner=False)
def load_geo_reference() -> tuple[dict | None, pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    env = load_env()
    bucket_url = env.get("HF_BUCKET_URL", "").rstrip("/")
    if not bucket_url:
        return None, None, None, None

    remote_base = f"{bucket_url}/IBGE/geo-mg"
    fs = hf_filesystem(env.get("HF_TOKEN"))
    geojson_path = f"{remote_base}/geojs-31-mun.json"
    tse_path = f"{remote_base}/municipios_brasileiros_tse.csv"
    municipios_path = f"{remote_base}/municipios.csv"
    regioes_path = f"{remote_base}/municipios.json"

    try:
        with fs.open(geojson_path, "r", encoding="utf-8") as source:
            geojson_mg = json.load(source)
        with fs.open(tse_path, "rb") as source:
            df_tse = pd.read_csv(
                source,
                usecols=["codigo_tse", "uf", "nome_municipio", "codigo_ibge"],
            )
        with fs.open(municipios_path, "rb") as source:
            df_municipios = pd.read_csv(
                source,
                usecols=["codigo_ibge", "nome", "latitude", "longitude"],
            )
    except Exception:
        return None, None, None, None

    df_tse = df_tse[df_tse["uf"].astype(str).str.upper() == "MG"].copy()
    df_tse["codigo_tse"] = pd.to_numeric(df_tse["codigo_tse"], errors="coerce").astype("Int64")
    df_tse["codigo_ibge"] = pd.to_numeric(df_tse["codigo_ibge"], errors="coerce").astype("Int64")
    df_tse["municipio_norm"] = df_tse["nome_municipio"].map(normalize_municipio_name)
    df_municipios["codigo_ibge"] = pd.to_numeric(
        df_municipios["codigo_ibge"], errors="coerce"
    ).astype("Int64")

    try:
        with fs.open(regioes_path, "r", encoding="utf-8") as source:
            raw_regioes = json.load(source)
        df_regioes = pd.DataFrame(raw_regioes)
        expected = {
            "municipio-id",
            "municipio-nome",
            "mesorregiao-nome",
            "regiao-imediata-nome",
        }
        if expected.issubset(df_regioes.columns):
            df_regioes = df_regioes[
                ["municipio-id", "municipio-nome", "mesorregiao-nome", "regiao-imediata-nome"]
            ].rename(
                columns={
                    "municipio-id": "codigo_ibge",
                    "municipio-nome": "municipio_ibge_nome",
                    "mesorregiao-nome": "mesorregiao_nome",
                    "regiao-imediata-nome": "regiao_imediata_nome",
                }
            )
            df_regioes["codigo_ibge"] = pd.to_numeric(
                df_regioes["codigo_ibge"], errors="coerce"
            ).astype("Int64")
        else:
            df_regioes = pd.DataFrame()
    except Exception:
        df_regioes = pd.DataFrame()

    return geojson_mg, df_tse, df_municipios, df_regioes


def normalize_municipio_name(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())

"""Small Deck.gl builders shared by the electoral maps."""

from __future__ import annotations

import math

import pydeck as pdk


def rgb(color: str, alpha: int = 255) -> list[int]:
    value = color.lstrip("#")
    return [int(value[index:index + 2], 16) for index in (0, 2, 4)] + [alpha]


def ramp(value: float, stops: list[str]) -> list[int]:
    value = max(0.0, min(1.0, float(value)))
    position = value * (len(stops) - 1)
    low = min(int(position), len(stops) - 2)
    fraction = position - low
    left, right = rgb(stops[low]), rgb(stops[low + 1])
    return [round(left[index] + fraction * (right[index] - left[index])) for index in range(3)] + [255]


# PyDeck 0.9.x rejects dict styles unless the provider is Mapbox.  Keep the
# provider-neutral default so deployments do not require a Mapbox token.
MAP_STYLE = None


def deck_geojson(
    features: list[dict], *, tooltip: str, layer_id: str,
    latitude: float = -18.5, longitude: float = -44.0, zoom: float = 5.4,
    pickable: bool = False, line_width: int = 1,
    line_color: list[int] | None = None,
) -> pdk.Deck:
    layer = pdk.Layer(
        "GeoJsonLayer",
        id=layer_id,
        data={"type": "FeatureCollection", "features": features},
        filled=True,
        stroked=True,
        pickable=pickable,
        auto_highlight=pickable,
        get_fill_color="properties.fill_color",
        get_line_color=line_color or [200, 220, 245, 170],
        line_width_min_pixels=line_width,
    )
    return pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=latitude, longitude=longitude, zoom=zoom),
        map_style=MAP_STYLE,
        tooltip={"html": tooltip, "style": {"backgroundColor": "#051022", "color": "#eaf2ff"}},
    )


def municipality_features(geojson: dict, values: dict[str, dict]) -> list[dict]:
    features = []
    for feature in geojson.get("features", []):
        code = str(feature.get("properties", {}).get("id", "")).zfill(7)
        properties = {"id": code, **values.get(code, {})}
        properties.setdefault("fill_color", rgb("#e8f1ff"))
        features.append({"type": "Feature", "geometry": feature["geometry"], "properties": properties})
    return features


def zoom_for_bounds(bounds: tuple[float, float, float, float]) -> float:
    minx, miny, maxx, maxy = bounds
    span = max(maxx - minx, (maxy - miny) * 1.5, 0.005)
    return max(5.0, min(12.5, math.log2(80.0 / span)))


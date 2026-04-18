"""Environmental and satellite data helpers.

Provides modular access to:
- OpenWeather current weather
- NASA GIBS satellite tile URL
- RainViewer radar tile URL

All functions degrade gracefully to deterministic fallbacks.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_CACHE: dict[str, dict[str, object]] = {}
_TTL = 600


def _cache_get(key: str):
    item = _CACHE.get(key)
    if not item:
        return None
    if time.time() - float(item["ts"]) > _TTL:
        _CACHE.pop(key, None)
        return None
    return item["value"]


def _cache_set(key: str, value):
    _CACHE[key] = {"ts": time.time(), "value": value}
    return value


def fetch_weather_data(lat: float, lng: float) -> Dict[str, object]:
    key = f"weather:{round(lat, 3)}:{round(lng, 3)}"
    cached = _cache_get(key)
    if cached:
        return cached

    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    fallback = {
        "success": True,
        "lat": round(float(lat), 5),
        "lng": round(float(lng), 5),
        "rainfall_mm": 0.0,
        "humidity": 70.0,
        "temperature_c": 28.0,
        "wind_speed_mps": 2.8,
        "source": "fallback",
        "summary": "Fallback weather profile",
    }
    if not api_key:
        return _cache_set(key, fallback)

    url = (
        "https://api.openweathermap.org/data/2.5/weather?"
        + urlencode(
            {
                "lat": f"{lat:.5f}",
                "lon": f"{lng:.5f}",
                "appid": api_key,
                "units": "metric",
            }
        )
    )

    try:
        with urlopen(Request(url, headers={"User-Agent": "DisasterDetector/1.0"}), timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, ValueError, TimeoutError):
        return _cache_set(key, fallback)

    main = payload.get("main", {})
    wind = payload.get("wind", {})
    rain = payload.get("rain", {})
    weather = (payload.get("weather") or [{}])[0]
    return _cache_set(
        key,
        {
            "success": True,
            "lat": round(float(lat), 5),
            "lng": round(float(lng), 5),
            "rainfall_mm": float(rain.get("1h") or rain.get("3h") or 0.0),
            "humidity": float(main.get("humidity") or 70.0),
            "temperature_c": float(main.get("temp") or 28.0),
            "wind_speed_mps": float(wind.get("speed") or 0.0),
            "source": "openweather",
            "summary": str(weather.get("description") or "current weather"),
        },
    )


def build_nasa_gibs_tile_url() -> Dict[str, object]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tile_url = (
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
        "MODIS_Terra_CorrectedReflectance_TrueColor/default/"
        f"{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
    )
    return {
        "success": True,
        "layer": "MODIS_Terra_CorrectedReflectance_TrueColor",
        "date": today,
        "satellite_tile_url": tile_url,
        "source": "nasa_gibs",
    }


def fetch_rainviewer_layer() -> Dict[str, object]:
    cached = _cache_get("rainviewer")
    if cached:
        return cached

    fallback = {
        "success": True,
        "rain_layer_url": "https://tilecache.rainviewer.com/v2/radar/nowcast_0/256/{z}/{x}/{y}/2/1_1.png",
        "source": "fallback",
    }

    try:
        with urlopen(Request("https://api.rainviewer.com/public/weather-maps.json", headers={"User-Agent": "DisasterDetector/1.0"}), timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, ValueError, TimeoutError):
        return _cache_set("rainviewer", fallback)

    host = str(payload.get("host") or "").rstrip("/")
    radar = payload.get("radar") or {}
    frames = radar.get("past") or radar.get("nowcast") or []
    if not host or not frames:
        return _cache_set("rainviewer", fallback)

    latest = frames[-1]
    path = str(latest.get("path") or "")
    if not path:
        return _cache_set("rainviewer", fallback)

    return _cache_set(
        "rainviewer",
        {
            "success": True,
            "rain_layer_url": f"{host}{path}/256/{{z}}/{{x}}/{{y}}/2/1_1.png",
            "generated": latest.get("time"),
            "source": "rainviewer",
        },
    )


def get_environmental_bundle(lat: float, lng: float) -> Dict[str, object]:
    weather = fetch_weather_data(lat, lng)
    satellite = build_nasa_gibs_tile_url()
    rain = fetch_rainviewer_layer()
    return {
        "success": True,
        "lat": round(float(lat), 5),
        "lng": round(float(lng), 5),
        "weather": weather,
        "satellite": satellite,
        "rain": rain,
    }

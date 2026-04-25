from __future__ import annotations

from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATASET_PATHS = {
    "flood": DATA_DIR / "flood.csv",
    "rainfall": DATA_DIR / "rainfall.csv",
    "disaster": DATA_DIR / "disaster.csv",
}

MODEL_ALGORITHM = "Random Forest"
MODEL_FORMULA = "0.5*ML + 0.3*Temporal + 0.2*Spatial"
FEATURE_NAMES = [
    "rainfall",
    "temperature",
    "humidity",
    "water_level",
    "river_discharge",
    "elevation",
    "population_density",
    "infrastructure",
    "historical_floods",
    "seismic_activity",
    "soil_moisture",
    "rainfall_climatology",
    "disaster_history_score",
]
ALERT_THRESHOLD = 0.7

REGION_PROFILES = {
    "Chennai": {
        "lat": 13.0827,
        "lon": 80.2707,
        "primary_hazard": "Flood",
        "rainfall": 228,
        "temperature": 31,
        "humidity": 82,
        "seismic_activity": 0.18,
        "soil_moisture": 0.78,
        "actual_risk_score": 0.74,
    },
    "Mumbai": {
        "lat": 19.076,
        "lon": 72.8777,
        "primary_hazard": "Flood",
        "rainfall": 245,
        "temperature": 30,
        "humidity": 85,
        "seismic_activity": 0.14,
        "soil_moisture": 0.8,
        "actual_risk_score": 0.77,
    },
    "Delhi": {
        "lat": 28.6139,
        "lon": 77.209,
        "primary_hazard": "Urban Heat / Seismic",
        "rainfall": 62,
        "temperature": 36,
        "humidity": 48,
        "seismic_activity": 0.46,
        "soil_moisture": 0.29,
        "actual_risk_score": 0.42,
    },
    "Assam": {
        "lat": 26.2006,
        "lon": 92.9376,
        "primary_hazard": "Flood",
        "rainfall": 265,
        "temperature": 29,
        "humidity": 88,
        "seismic_activity": 0.54,
        "soil_moisture": 0.84,
        "actual_risk_score": 0.86,
    },
    "Uttarakhand": {
        "lat": 30.0668,
        "lon": 79.0193,
        "primary_hazard": "Landslide",
        "rainfall": 176,
        "temperature": 23,
        "humidity": 72,
        "seismic_activity": 0.63,
        "soil_moisture": 0.68,
        "actual_risk_score": 0.71,
    },
    "Himachal": {
        "lat": 31.1048,
        "lon": 77.1734,
        "primary_hazard": "Landslide",
        "rainfall": 158,
        "temperature": 21,
        "humidity": 69,
        "seismic_activity": 0.58,
        "soil_moisture": 0.65,
        "actual_risk_score": 0.67,
    },
}

REGION_HISTORY = {
    "Chennai": [0.62, 0.66, 0.68, 0.7, 0.72, 0.74, 0.76],
    "Mumbai": [0.65, 0.67, 0.7, 0.71, 0.73, 0.75, 0.78],
    "Delhi": [0.36, 0.38, 0.39, 0.41, 0.42, 0.44, 0.45],
    "Assam": [0.74, 0.77, 0.79, 0.81, 0.83, 0.85, 0.87],
    "Uttarakhand": [0.58, 0.61, 0.64, 0.67, 0.69, 0.71, 0.73],
    "Himachal": [0.55, 0.57, 0.6, 0.62, 0.64, 0.66, 0.68],
}

RAINFALL_REGION_MAP = {
    "Tamil Nadu": "Chennai",
    "Konkan & Goa": "Mumbai",
    "Haryana Delhi & Chandigarh": "Delhi",
    "Assam & Meghalaya": "Assam",
    "Uttarakhand": "Uttarakhand",
    "Himachal Pradesh": "Himachal",
}

ZONE_PROFILES = {
    "flood": [
        {
            "id": "flood-chennai-coastal",
            "region": "Chennai",
            "zone_name": "North Chennai Basin",
            "lat": 13.145,
            "lon": 80.285,
            "radius_km": 32,
            "timestamp": "2026-04-18T10:00:00Z",
            "rainfall": 228,
            "water_level": 0.76,
            "river_level": 0.72,
            "elevation_inverse": 0.82,
            "soil_moisture": 0.78,
        },
        {
            "id": "flood-mumbai-coastal",
            "region": "Mumbai",
            "zone_name": "Mumbai Coastal Belt",
            "lat": 19.092,
            "lon": 72.89,
            "radius_km": 30,
            "timestamp": "2026-04-18T10:00:00Z",
            "rainfall": 245,
            "water_level": 0.8,
            "river_level": 0.74,
            "elevation_inverse": 0.79,
            "soil_moisture": 0.8,
        },
        {
            "id": "flood-assam-brahmaputra",
            "region": "Assam",
            "zone_name": "Brahmaputra Floodplain",
            "lat": 26.24,
            "lon": 91.71,
            "radius_km": 45,
            "timestamp": "2026-04-18T10:00:00Z",
            "rainfall": 265,
            "water_level": 0.84,
            "river_level": 0.88,
            "elevation_inverse": 0.73,
            "soil_moisture": 0.84,
        },
    ],
    "earthquake": [
        {
            "id": "earthquake-delhi-ridge",
            "region": "Delhi",
            "zone_name": "Delhi Ridge Seismic Zone",
            "lat": 28.67,
            "lon": 77.19,
            "radius_km": 36,
            "timestamp": "2026-04-18T10:00:00Z",
            "magnitude": 5.6,
            "cluster_density": 0.58,
            "shallow_depth": 0.66,
            "ground_stress": 0.54,
        },
        {
            "id": "earthquake-uttarakhand-main",
            "region": "Uttarakhand",
            "zone_name": "Garhwal Fault Belt",
            "lat": 30.32,
            "lon": 78.04,
            "radius_km": 42,
            "timestamp": "2026-04-18T10:00:00Z",
            "magnitude": 6.1,
            "cluster_density": 0.71,
            "shallow_depth": 0.74,
            "ground_stress": 0.68,
        },
        {
            "id": "earthquake-himachal-main",
            "region": "Himachal",
            "zone_name": "Kangra Seismic Arc",
            "lat": 31.58,
            "lon": 76.94,
            "radius_km": 40,
            "timestamp": "2026-04-18T10:00:00Z",
            "magnitude": 5.9,
            "cluster_density": 0.68,
            "shallow_depth": 0.7,
            "ground_stress": 0.64,
        },
    ],
    "landslide": [
        {
            "id": "landslide-uttarakhand-slope",
            "region": "Uttarakhand",
            "zone_name": "Alaknanda Valley Slopes",
            "lat": 30.41,
            "lon": 79.32,
            "radius_km": 34,
            "timestamp": "2026-04-18T10:00:00Z",
            "slope": 0.82,
            "soil_moisture": 0.68,
            "rainfall": 176,
            "terrain_instability": 0.74,
        },
        {
            "id": "landslide-himachal-slope",
            "region": "Himachal",
            "zone_name": "Shimla Hill Belt",
            "lat": 31.11,
            "lon": 77.24,
            "radius_km": 30,
            "timestamp": "2026-04-18T10:00:00Z",
            "slope": 0.78,
            "soil_moisture": 0.65,
            "rainfall": 158,
            "terrain_instability": 0.69,
        },
        {
            "id": "landslide-assam-hills",
            "region": "Assam",
            "zone_name": "Barak Valley Hills",
            "lat": 24.85,
            "lon": 92.78,
            "radius_km": 28,
            "timestamp": "2026-04-18T10:00:00Z",
            "slope": 0.64,
            "soil_moisture": 0.72,
            "rainfall": 214,
            "terrain_instability": 0.62,
        },
    ],
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin1")


def _column_by_prefix(df: pd.DataFrame, prefix: str) -> str | None:
    prefix = prefix.lower()
    for column in df.columns:
        if str(column).lower().startswith(prefix):
            return column
    return None


def _numeric(series: pd.Series, default: float = 0.0) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.isna().all():
        return values.fillna(default)
    return values.fillna(values.median())


def _nearest_region_name(lat: float, lon: float) -> str | None:
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None
    if pd.isna(lat) or pd.isna(lon):
        return None
    return min(
        REGION_PROFILES,
        key=lambda region: _distance_km(lat, lon, REGION_PROFILES[region]["lat"], REGION_PROFILES[region]["lon"]),
    )


def _region_from_text(*parts: object) -> str | None:
    text = " ".join(str(part) for part in parts if pd.notna(part)).lower()
    keyword_map = {
        "Chennai": ["chennai", "tamil", "cuddalore", "pondicherry"],
        "Mumbai": ["mumbai", "maharashtra", "konkan", "bombay"],
        "Delhi": ["delhi", "haryana", "chandigarh"],
        "Assam": ["assam", "brahmaputra", "meghalaya", "bengal"],
        "Uttarakhand": ["uttarakhand", "garhwal", "dehradun"],
        "Himachal": ["himachal", "kangra", "shimla"],
    }
    for region, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            return region
    return None


def _rainfall_score(value: float) -> float:
    return _clamp(float(value) / 300.0)


def compute_temporal(df: pd.DataFrame) -> float:
    if df.empty or "rainfall" not in df:
        return 0.0
    rainfall = pd.to_numeric(df["rainfall"], errors="coerce").dropna()
    if rainfall.empty:
        return 0.0
    return float(rainfall.rolling(7, min_periods=1).mean().iloc[-1])


def compute_spatial(df: pd.DataFrame) -> float:
    if df.empty or "rainfall" not in df or "region" not in df:
        return 0.0
    grouped = df.groupby("region")["rainfall"].mean()
    if grouped.empty:
        return 0.0
    return float(grouped.mean())


def _normalise_rainfall_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame(columns=["region", "subdivision", "year", "month", "month_number", "rainfall"])

    month_columns = [month for month in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"] if month in raw_df]
    if not month_columns or "SUBDIVISION" not in raw_df or "YEAR" not in raw_df:
        return pd.DataFrame(columns=["region", "subdivision", "year", "month", "month_number", "rainfall"])

    month_number = {month: index + 1 for index, month in enumerate(month_columns)}
    rainfall = raw_df.melt(
        id_vars=["SUBDIVISION", "YEAR"],
        value_vars=month_columns,
        var_name="month",
        value_name="rainfall",
    )
    rainfall["rainfall"] = pd.to_numeric(rainfall["rainfall"], errors="coerce")
    rainfall["year"] = pd.to_numeric(rainfall["YEAR"], errors="coerce")
    rainfall["month_number"] = rainfall["month"].map(month_number)
    rainfall["subdivision"] = rainfall["SUBDIVISION"]
    rainfall["region"] = rainfall["subdivision"].map(RAINFALL_REGION_MAP).fillna(rainfall["subdivision"])
    rainfall = rainfall.dropna(subset=["rainfall", "year", "month_number"])
    rainfall = rainfall.sort_values(["region", "year", "month_number"])
    return rainfall[["region", "subdivision", "year", "month", "month_number", "rainfall"]]


def _normalise_disaster_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame(columns=["region", "event_weight"])

    lat_col = _column_by_prefix(raw_df, "Latitude")
    lon_col = _column_by_prefix(raw_df, "Longitude")
    location_col = _column_by_prefix(raw_df, "Location")
    admin_col = _column_by_prefix(raw_df, "Admin Units")
    event_col = _column_by_prefix(raw_df, "Event Name")
    deaths_col = _column_by_prefix(raw_df, "Total Deaths")
    affected_col = _column_by_prefix(raw_df, "Total Affected")
    magnitude_col = _column_by_prefix(raw_df, "Magnitude")

    disaster = pd.DataFrame(index=raw_df.index)
    if lat_col and lon_col:
        disaster["region"] = [
            _nearest_region_name(lat, lon) for lat, lon in zip(raw_df[lat_col], raw_df[lon_col])
        ]
    else:
        disaster["region"] = None

    text_columns = [column for column in [location_col, admin_col, event_col] if column]
    if text_columns:
        text_regions = raw_df[text_columns].apply(lambda row: _region_from_text(*row.values), axis=1)
        disaster["region"] = disaster["region"].fillna(text_regions)

    deaths = _numeric(raw_df[deaths_col], 0.0) if deaths_col else pd.Series(0.0, index=raw_df.index)
    affected = _numeric(raw_df[affected_col], 0.0) if affected_col else pd.Series(0.0, index=raw_df.index)
    magnitude = _numeric(raw_df[magnitude_col], 0.0) if magnitude_col else pd.Series(0.0, index=raw_df.index)
    disaster["event_weight"] = 1.0 + (deaths / 10000.0) + (affected / 1000000.0) + (magnitude / 10.0)
    disaster = disaster.dropna(subset=["region"])
    return disaster[["region", "event_weight"]]


def _disaster_score_map(disaster_df: pd.DataFrame) -> dict[str, float]:
    if disaster_df.empty:
        return {region: 0.0 for region in REGION_PROFILES}
    weights = disaster_df.groupby("region")["event_weight"].sum()
    max_weight = float(weights.max()) if not weights.empty else 1.0
    if max_weight <= 0:
        max_weight = 1.0
    return {region: round(_clamp(float(weights.get(region, 0.0)) / max_weight), 4) for region in REGION_PROFILES}


def _label_from_features(features: dict) -> int:
    weighted_score = (
        0.24 * _rainfall_score(features.get("rainfall", 0.0))
        + 0.12 * _clamp(float(features.get("temperature", 0.0)) / 45.0)
        + 0.16 * _clamp(float(features.get("humidity", 0.0)) / 100.0)
        + 0.16 * _clamp(float(features.get("water_level", 0.0)) / 10.0)
        + 0.12 * _clamp(float(features.get("river_discharge", 0.0)) / 5000.0)
        + 0.12 * _clamp(float(features.get("soil_moisture", 0.0)))
        + 0.08 * _clamp(float(features.get("disaster_history_score", 0.0)))
    )
    return 1 if weighted_score >= 0.52 else 0


def _fallback_training_frame() -> pd.DataFrame:
    rows = []
    for region, profile in REGION_PROFILES.items():
        for index in range(36):
            offset = (index % 12) - 5.5
            features = {
                "region": region,
                "rainfall": max(0.0, profile["rainfall"] + offset * 8.0),
                "temperature": max(0.0, profile["temperature"] + offset * 0.35),
                "humidity": _clamp((profile["humidity"] + offset * 1.5) / 100.0) * 100.0,
                "water_level": _clamp(0.45 + profile["soil_moisture"] * 0.45 + offset * 0.02) * 10.0,
                "river_discharge": max(250.0, profile["rainfall"] * 15.0 + offset * 80.0),
                "elevation": 250.0 + profile["lat"] * 12.0,
                "population_density": 2500.0 + profile["lon"] * 40.0,
                "infrastructure": 1.0 if index % 3 else 0.0,
                "historical_floods": 1.0 if profile["primary_hazard"] == "Flood" else 0.0,
                "seismic_activity": profile["seismic_activity"],
                "soil_moisture": profile["soil_moisture"],
                "rainfall_climatology": profile["rainfall"] * 0.55,
                "disaster_history_score": profile["actual_risk_score"],
            }
            features["label"] = _label_from_features(features)
            rows.append(features)
    return pd.DataFrame(rows)


def _normalise_flood_dataset(
    raw_df: pd.DataFrame,
    rainfall_df: pd.DataFrame,
    disaster_scores: dict[str, float],
) -> pd.DataFrame:
    if raw_df.empty:
        return _fallback_training_frame()

    column_map = {
        "lat": _column_by_prefix(raw_df, "Latitude"),
        "lon": _column_by_prefix(raw_df, "Longitude"),
        "rainfall": _column_by_prefix(raw_df, "Rainfall"),
        "temperature": _column_by_prefix(raw_df, "Temperature"),
        "humidity": _column_by_prefix(raw_df, "Humidity"),
        "river_discharge": _column_by_prefix(raw_df, "River Discharge"),
        "water_level": _column_by_prefix(raw_df, "Water Level"),
        "elevation": _column_by_prefix(raw_df, "Elevation"),
        "population_density": _column_by_prefix(raw_df, "Population Density"),
        "infrastructure": _column_by_prefix(raw_df, "Infrastructure"),
        "historical_floods": _column_by_prefix(raw_df, "Historical Floods"),
        "label": _column_by_prefix(raw_df, "Flood Occurred"),
    }
    required = ["lat", "lon", "rainfall", "temperature", "humidity", "label"]
    if any(column_map[name] is None for name in required):
        return _fallback_training_frame()

    flood = pd.DataFrame(index=raw_df.index)
    flood["region"] = [
        _nearest_region_name(lat, lon) for lat, lon in zip(raw_df[column_map["lat"]], raw_df[column_map["lon"]])
    ]
    for name in [
        "rainfall",
        "temperature",
        "humidity",
        "river_discharge",
        "water_level",
        "elevation",
        "population_density",
        "infrastructure",
        "historical_floods",
        "label",
    ]:
        source = column_map.get(name)
        flood[name] = _numeric(raw_df[source], 0.0) if source else 0.0

    rainfall_max = max(float(flood["rainfall"].quantile(0.95)), 1.0)
    humidity_score = (flood["humidity"] / 100.0).clip(0.0, 1.0)
    rainfall_component = (flood["rainfall"] / rainfall_max).clip(0.0, 1.0)
    water_component = (flood["water_level"] / max(float(flood["water_level"].quantile(0.95)), 1.0)).clip(0.0, 1.0)
    flood["soil_moisture"] = ((0.4 * rainfall_component) + (0.35 * humidity_score) + (0.25 * water_component)).clip(0.0, 1.0)

    flood["seismic_activity"] = flood["region"].map(
        {region: profile["seismic_activity"] for region, profile in REGION_PROFILES.items()}
    )

    if not rainfall_df.empty:
        rainfall_means = rainfall_df.groupby("region")["rainfall"].mean()
        global_rainfall = float(rainfall_df["rainfall"].mean())
        flood["rainfall_climatology"] = flood["region"].map(rainfall_means).fillna(global_rainfall)
    else:
        flood["rainfall_climatology"] = flood["rainfall"].mean()

    flood["disaster_history_score"] = flood["region"].map(disaster_scores).fillna(0.0)
    flood = flood.dropna(subset=["region"])
    for feature in FEATURE_NAMES:
        flood[feature] = _numeric(flood[feature], 0.0)
    flood["label"] = pd.to_numeric(flood["label"], errors="coerce").fillna(0).round().clip(0, 1).astype(int)
    return flood[["region", *FEATURE_NAMES, "label"]]


def _build_region_summaries(training_df: pd.DataFrame, rainfall_df: pd.DataFrame) -> dict[str, dict]:
    summaries = {}
    latest_year = int(rainfall_df["year"].max()) if not rainfall_df.empty else 2026
    for region, profile in REGION_PROFILES.items():
        subset = training_df[training_df["region"] == region]
        if subset.empty:
            subset = training_df

        snapshot = {}
        high_signal_features = {
            "rainfall",
            "humidity",
            "water_level",
            "river_discharge",
            "soil_moisture",
            "population_density",
            "rainfall_climatology",
            "disaster_history_score",
        }
        for feature in FEATURE_NAMES:
            source = subset[feature]
            value = source.quantile(0.7) if feature in high_signal_features else source.median()
            if pd.isna(value):
                value = 0.0
            snapshot[feature] = round(float(value), 4)

        snapshot["infrastructure"] = int(round(float(subset["infrastructure"].mean())))
        snapshot["historical_floods"] = int(round(float(subset["historical_floods"].mean())))
        actual_risk_score = round(float(subset["label"].mean()), 4)

        region_rainfall = rainfall_df[rainfall_df["region"] == region].tail(7)
        temporal_history = [_rainfall_score(value) for value in region_rainfall["rainfall"].tolist()]
        if not temporal_history:
            temporal_history = REGION_HISTORY[region]

        summaries[region] = {
            "region": region,
            "lat": profile["lat"],
            "lon": profile["lon"],
            "primary_hazard": profile["primary_hazard"],
            **snapshot,
            "actual_risk_score": actual_risk_score,
            "actual_label": 1 if actual_risk_score >= 0.5 else 0,
            "actual_risk_level": risk_level_from_score(actual_risk_score),
            "timestamp": f"{latest_year}-12-31T00:00:00Z",
            "temporal_history": [round(value, 4) for value in temporal_history],
        }
    return summaries


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def risk_level_from_score(score: float) -> str:
    if score >= 0.7:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


@lru_cache(maxsize=1)
def load_model_bundle() -> dict:
    raw_flood = _read_csv(DATASET_PATHS["flood"])
    raw_rainfall = _read_csv(DATASET_PATHS["rainfall"])
    raw_disaster = _read_csv(DATASET_PATHS["disaster"])

    rainfall_df = _normalise_rainfall_dataset(raw_rainfall)
    disaster_df = _normalise_disaster_dataset(raw_disaster)
    disaster_scores = _disaster_score_map(disaster_df)
    training_df = _normalise_flood_dataset(raw_flood, rainfall_df, disaster_scores)

    features = training_df[FEATURE_NAMES].copy()
    labels = training_df["label"].astype(int)
    feature_medians = features.median(numeric_only=True).fillna(0.0)
    features = features.fillna(feature_medians)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    model = RandomForestClassifier(
        n_estimators=180,
        max_depth=6,
        random_state=42,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    region_summaries = _build_region_summaries(training_df, rainfall_df)

    return {
        "model": model,
        "training_df": training_df,
        "rainfall_df": rainfall_df,
        "disaster_df": disaster_df,
        "feature_medians": feature_medians,
        "region_summaries": region_summaries,
        "metrics": {
            "accuracy": round(accuracy_score(y_test, predictions), 4),
            "precision": round(precision_score(y_test, predictions, zero_division=0), 4),
            "recall": round(recall_score(y_test, predictions, zero_division=0), 4),
        },
        "feature_importance": {
            name: round(float(value), 4)
            for name, value in zip(FEATURE_NAMES, model.feature_importances_)
        },
        "dataset_rows": {
            "flood": int(len(raw_flood)),
            "rainfall": int(len(raw_rainfall)),
            "disaster": int(len(raw_disaster)),
            "training": int(len(training_df)),
        },
    }


def get_feature_importance() -> dict:
    return load_model_bundle()["feature_importance"]


def get_model_metrics() -> dict:
    return load_model_bundle()["metrics"]


def get_dataset_metadata() -> dict:
    bundle = load_model_bundle()
    return {
        "files": {name: str(path.relative_to(BASE_DIR)) for name, path in DATASET_PATHS.items()},
        "rows": bundle["dataset_rows"],
    }


def get_region_snapshot(region: str) -> dict:
    return dict(load_model_bundle()["region_summaries"][region])


def get_temporal_factor(region: str) -> float:
    rainfall_df = load_model_bundle()["rainfall_df"]
    region_rainfall = rainfall_df[rainfall_df["region"] == region].sort_values(["year", "month_number"])
    if region_rainfall.empty:
        return round(sum(REGION_HISTORY[region]) / len(REGION_HISTORY[region]), 4)
    temporal_rainfall = compute_temporal(region_rainfall)
    return round(_rainfall_score(temporal_rainfall), 4)


def get_spatial_influence(region: str) -> float:
    rainfall_df = load_model_bundle()["rainfall_df"]
    if rainfall_df.empty:
        return round(REGION_PROFILES[region]["actual_risk_score"], 4)

    grouped = rainfall_df.groupby("region")["rainfall"].mean()
    nearby_regions = sorted(
        REGION_PROFILES,
        key=lambda nearby_region: _distance_km(
            REGION_PROFILES[region]["lat"],
            REGION_PROFILES[region]["lon"],
            REGION_PROFILES[nearby_region]["lat"],
            REGION_PROFILES[nearby_region]["lon"],
        ),
    )[:3]
    nearby_values = [float(grouped[item]) for item in nearby_regions if item in grouped]
    spatial_rainfall = sum(nearby_values) / len(nearby_values) if nearby_values else compute_spatial(rainfall_df)
    return round(_rainfall_score(spatial_rainfall), 4)


def predict_region_risk(region: str) -> dict:
    snapshot = get_region_snapshot(region)
    bundle = load_model_bundle()
    model = bundle["model"]
    feature_vector = pd.DataFrame([{name: snapshot.get(name, bundle["feature_medians"].get(name, 0.0)) for name in FEATURE_NAMES}])
    feature_vector = feature_vector.fillna(bundle["feature_medians"])
    ml_prediction = float(model.predict_proba(feature_vector)[0][1])
    temporal_score = get_temporal_factor(region)
    spatial_score = get_spatial_influence(region)
    probability = (0.5 * ml_prediction) + (0.3 * temporal_score) + (0.2 * spatial_score)
    probability = round(min(1.0, max(0.0, probability)), 4)
    level = risk_level_from_score(probability)

    drivers = []
    if snapshot["rainfall"] >= bundle["training_df"]["rainfall"].quantile(0.7):
        drivers.append("elevated rainfall")
    if snapshot["water_level"] >= bundle["training_df"]["water_level"].quantile(0.7):
        drivers.append("high water level")
    if temporal_score >= 0.55:
        drivers.append("sustained recent rainfall")
    if spatial_score >= 0.45:
        drivers.append("nearby-region rainfall pressure")
    if not drivers:
        drivers.append("moderate current environmental signals")

    analysis = (
        f"{level} risk for {region} due to {', '.join(drivers[:3])}. "
        "The score combines the trained Random Forest probability with temporal and spatial rainfall context."
    )

    return {
        "region": region,
        "risk_score": probability,
        "risk_level": level,
        "explanation": analysis,
        "analysis": analysis,
        "ml_prediction": round(ml_prediction, 4),
        "ml_score": round(ml_prediction, 4),
        "temporal_factor": temporal_score,
        "temporal_score": temporal_score,
        "spatial_influence": spatial_score,
        "spatial_score": spatial_score,
        "algorithm": MODEL_ALGORITHM,
        "formula": MODEL_FORMULA,
    }


def _flood_zone_risk(zone: dict) -> float:
    return _clamp(
        (0.4 * (zone["rainfall"] / 300.0))
        + (0.2 * zone["elevation_inverse"])
        + (0.2 * zone["river_level"])
        + (0.2 * zone["soil_moisture"])
    )


def _earthquake_zone_risk(zone: dict) -> float:
    return _clamp(
        (0.45 * (zone["magnitude"] / 8.0))
        + (0.35 * zone["cluster_density"])
        + (0.20 * zone["shallow_depth"])
    )


def _landslide_zone_risk(zone: dict) -> float:
    return _clamp(
        (0.35 * zone["slope"])
        + (0.25 * zone["soil_moisture"])
        + (0.25 * (zone["rainfall"] / 300.0))
        + (0.15 * zone["terrain_instability"])
    )


def _disaster_label(disaster: str) -> str:
    labels = {
        "flood": "Flood",
        "earthquake": "Earthquake",
        "landslide": "Landslide",
    }
    return labels[disaster]


def _zone_risk_score(disaster: str, zone: dict) -> float:
    if disaster == "flood":
        return round(_flood_zone_risk(zone), 4)
    if disaster == "earthquake":
        return round(_earthquake_zone_risk(zone), 4)
    return round(_landslide_zone_risk(zone), 4)


def get_disaster_items(disaster: str) -> list[dict]:
    items = []
    for zone in ZONE_PROFILES[disaster]:
        risk_score = _zone_risk_score(disaster, zone)
        level = risk_level_from_score(risk_score)
        items.append(
            {
                **zone,
                "place": zone["zone_name"],
                "location": zone["zone_name"],
                "latitude": zone["lat"],
                "longitude": zone["lon"],
                "disaster": _disaster_label(disaster),
                "risk_score": risk_score,
                "risk_level": level,
            }
        )
    items.sort(key=lambda item: item["risk_score"], reverse=True)
    return items


def get_dashboard_payload(disaster: str) -> dict:
    items = get_disaster_items(disaster)
    top_item = items[0] if items else None
    return {
        "disaster": disaster,
        "latest_data": items,
        "zones": items,
        "prediction": top_item,
    }


def list_regions() -> list[dict]:
    regions = []
    for region in REGION_PROFILES:
        snapshot = get_region_snapshot(region)
        prediction = predict_region_risk(region)
        regions.append(
            {
                "region": region,
                "lat": snapshot["lat"],
                "lon": snapshot["lon"],
                "primary_hazard": snapshot["primary_hazard"],
                "risk_score": prediction["risk_score"],
                "risk_level": prediction["risk_level"],
                "actual_risk_score": snapshot["actual_risk_score"],
                "actual_risk_level": snapshot["actual_risk_level"],
                "timestamp": snapshot["timestamp"],
                "rainfall": snapshot["rainfall"],
                "temperature": snapshot["temperature"],
                "humidity": snapshot["humidity"],
                "seismic_activity": snapshot["seismic_activity"],
                "soil_moisture": snapshot["soil_moisture"],
                "ml_prediction": prediction["ml_prediction"],
                "temporal_factor": prediction["temporal_factor"],
                "spatial_influence": prediction["spatial_influence"],
            }
        )
    return regions

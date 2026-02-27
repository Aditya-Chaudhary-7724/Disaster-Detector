"""Feature engineering utilities for hybrid disaster prediction.

US-3 enhancements included here:
- Temporal smoothing (rolling means)
- Missing value imputation
- Geo-spatial clustering (KMeans)
- StandardScaler normalization
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

BASE_FEATURES = [
    "latitude",
    "longitude",
    "rainfall_24h_mm",
    "rainfall_7d_mm",
    "soil_moisture",
    "slope_deg",
    "ndvi",
    "plant_density",
    "seismic_magnitude",
    "depth_km",
    "weather_temp_c",
    "weather_humidity",
    "weather_pressure_hpa",
    "weather_rain_3h_mm",
]

ROLLING_TARGETS = ["rainfall_24h_mm", "soil_moisture", "slope_deg", "seismic_magnitude"]
ROLLING_FEATURES = [f"{c}_roll3" for c in ROLLING_TARGETS]
AUX_FEATURES = ["geo_cluster"]
MODEL_FEATURES = BASE_FEATURES + ROLLING_FEATURES + AUX_FEATURES


@dataclass
class FeatureArtifacts:
    imputer: SimpleImputer
    scaler: StandardScaler
    kmeans: KMeans
    feature_columns: List[str]


def _to_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out[col] = out[col].replace([np.inf, -np.inf], np.nan)
    return out


def _ensure_timestamp(df: pd.DataFrame) -> pd.Series:
    if "timestamp" in df.columns:
        return pd.to_datetime(df["timestamp"], errors="coerce")
    return pd.Series(pd.NaT, index=df.index)


def _normalize_disaster(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "disaster" in out.columns and "disaster_type" not in out.columns:
        out["disaster_type"] = out["disaster"]
    out["disaster_type"] = out.get("disaster_type", "unknown").astype(str).str.lower()

    if "seismic_mag" in out.columns and "seismic_magnitude" not in out.columns:
        out["seismic_magnitude"] = out["seismic_mag"]
    return out


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    out = _normalize_disaster(df)
    out = _to_numeric(out, BASE_FEATURES)

    out["timestamp"] = _ensure_timestamp(out)
    out = out.sort_values(["disaster_type", "timestamp"], na_position="last").copy()

    for base in ROLLING_TARGETS:
        out[f"{base}_roll3"] = (
            out.groupby("disaster_type", dropna=False)[base]
            .transform(lambda s: s.rolling(window=3, min_periods=1).mean())
            .astype(float)
        )

    return out


def fit_feature_artifacts(df: pd.DataFrame) -> Tuple[pd.DataFrame, FeatureArtifacts]:
    feat_df = add_temporal_features(df)

    imputer = SimpleImputer(strategy="median")
    imputed = imputer.fit_transform(feat_df[BASE_FEATURES + ROLLING_FEATURES])
    imputed_df = pd.DataFrame(imputed, columns=BASE_FEATURES + ROLLING_FEATURES, index=feat_df.index)

    coords = imputed_df[["latitude", "longitude"]].to_numpy()
    n_clusters = max(2, min(6, len(coords)))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    geo_cluster = kmeans.fit_predict(coords)
    imputed_df["geo_cluster"] = geo_cluster

    scaler = StandardScaler()
    scaled = scaler.fit_transform(imputed_df[MODEL_FEATURES])
    scaled_df = pd.DataFrame(scaled, columns=MODEL_FEATURES, index=feat_df.index)

    artifacts = FeatureArtifacts(
        imputer=imputer,
        scaler=scaler,
        kmeans=kmeans,
        feature_columns=MODEL_FEATURES,
    )
    return scaled_df, artifacts


def transform_with_artifacts(df: pd.DataFrame, artifacts: FeatureArtifacts) -> pd.DataFrame:
    feat_df = add_temporal_features(df)

    imputed = artifacts.imputer.transform(feat_df[BASE_FEATURES + ROLLING_FEATURES])
    imputed_df = pd.DataFrame(imputed, columns=BASE_FEATURES + ROLLING_FEATURES, index=feat_df.index)

    coords = imputed_df[["latitude", "longitude"]].to_numpy()
    geo_cluster = artifacts.kmeans.predict(coords)
    imputed_df["geo_cluster"] = geo_cluster

    scaled = artifacts.scaler.transform(imputed_df[artifacts.feature_columns])
    return pd.DataFrame(scaled, columns=artifacts.feature_columns, index=feat_df.index)

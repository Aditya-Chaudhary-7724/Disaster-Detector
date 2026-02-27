"""ML serving utilities for disaster risk prediction."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

MODEL_PATH = Path(__file__).parent / "models" / "disaster_predictor.pkl"
DATASET_PATH = Path(__file__).parent / "datasets" / "disaster_dataset.csv"

FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "rainfall_24h_mm",
    "soil_moisture",
    "slope_deg",
    "ndvi",
    "plant_density",
    "seismic_magnitude",
    "depth_km",
]
LABEL_COLUMN = "risk_label"

MODEL_CACHE = None
MODEL_METADATA: Dict[str, object] = {}


def _safe_imports():
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    return joblib, pd, RandomForestClassifier, accuracy_score, train_test_split, Pipeline, StandardScaler


def _normalize_columns(df):
    if "seismic_mag" in df.columns and "seismic_magnitude" not in df.columns:
        df = df.rename(columns={"seismic_mag": "seismic_magnitude"})
    return df


def train_model(force: bool = False) -> Dict[str, object]:
    global MODEL_CACHE, MODEL_METADATA
    joblib, pd, RandomForestClassifier, accuracy_score, train_test_split, Pipeline, StandardScaler = _safe_imports()

    if MODEL_PATH.exists() and not force:
        model = joblib.load(MODEL_PATH)
        MODEL_CACHE = model
        MODEL_METADATA = {"method": "ML", "model_path": str(MODEL_PATH), "accuracy": None}
        return MODEL_METADATA

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset missing: {DATASET_PATH}")

    df = _normalize_columns(pd.read_csv(DATASET_PATH))
    missing = [c for c in FEATURE_COLUMNS + [LABEL_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    X = df[FEATURE_COLUMNS]
    y = df[LABEL_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=350,
                    max_depth=18,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    acc = float(accuracy_score(y_test, model.predict(X_test)))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    MODEL_CACHE = model
    MODEL_METADATA = {"method": "ML", "model_path": str(MODEL_PATH), "accuracy": round(acc, 4)}
    return MODEL_METADATA


def _as_vector(payload: Dict[str, object]) -> List[float]:
    def f(key: str, default: float = 0.0) -> float:
        try:
            return float(payload.get(key, default) or default)
        except (TypeError, ValueError):
            return default

    return [
        f("latitude") or f("lat"),
        f("longitude") or f("lon"),
        f("rainfall_24h_mm"),
        f("soil_moisture"),
        f("slope_deg"),
        f("ndvi", 0.5),
        f("plant_density", 0.5),
        f("seismic_magnitude") or f("seismic_mag"),
        f("depth_km"),
    ]


def ensure_model_loaded() -> Tuple[object, Dict[str, object]]:
    global MODEL_CACHE
    if MODEL_CACHE is not None:
        return MODEL_CACHE, MODEL_METADATA
    train_model(force=False)
    return MODEL_CACHE, MODEL_METADATA


def predict_with_model(payload: Dict[str, object]) -> Dict[str, object]:
    _, pd, _, _, _, _, _ = _safe_imports()

    model, metadata = ensure_model_loaded()
    X = pd.DataFrame([_as_vector(payload)], columns=FEATURE_COLUMNS)

    risk_level = str(model.predict(X)[0])
    confidence = None
    if hasattr(model, "predict_proba"):
        confidence = float(max(model.predict_proba(X)[0]))

    # Pull RF importances from pipeline step
    feature_importance = {}
    if hasattr(model, "named_steps") and "rf" in model.named_steps:
        rf = model.named_steps["rf"]
        if hasattr(rf, "feature_importances_"):
            for name, val in zip(FEATURE_COLUMNS, rf.feature_importances_):
                feature_importance[name] = round(float(val), 4)

    return {
        "risk_level": risk_level,
        "confidence": round(confidence, 4) if confidence is not None else None,
        "method": "ML",
        "feature_importance": feature_importance,
        "model_accuracy": metadata.get("accuracy"),
    }

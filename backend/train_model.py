"""Train production RandomForest model for disaster risk prediction.

Academic notes:
- Random Forest is used because ensemble bagging reduces variance vs a single tree.
- It handles non-linear interactions between hydro-meteorological and seismic features.
- Bias-variance tradeoff: deeper trees reduce bias, bagging reduces variance.
- Standardization is included in pipeline for feature-space consistency and future model swaps.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA_PATH = Path(__file__).parent / "datasets" / "disaster_dataset.csv"
MODEL_PATH = Path(__file__).parent / "models" / "disaster_predictor.pkl"

FEATURES = [
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
LABEL = "risk_label"


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    if "seismic_mag" in df.columns and "seismic_magnitude" not in df.columns:
        df = df.rename(columns={"seismic_mag": "seismic_magnitude"})

    missing = [c for c in FEATURES + [LABEL] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    X = df[FEATURES]
    y = df[LABEL]

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
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=["Low", "Medium", "High"])

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print("Model trained successfully")
    print(f"Model path: {MODEL_PATH}")
    print(f"Accuracy: {acc:.4f}")
    print(f"Precision (weighted): {precision:.4f}")
    print(f"Recall (weighted): {recall:.4f}")
    print(f"F1 (weighted): {f1:.4f}")
    print("Confusion Matrix [Low, Medium, High]:")
    print(cm)
    print("Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))


if __name__ == "__main__":
    main()

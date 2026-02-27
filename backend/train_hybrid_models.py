"""Train hybrid logistic-regression + random-forest models for disaster prediction."""

from __future__ import annotations

from ml_hybrid_predictor import train_hybrid_models


if __name__ == "__main__":
    meta = train_hybrid_models(force=True)
    print("Hybrid models trained.")
    print(meta.get("meta", meta))

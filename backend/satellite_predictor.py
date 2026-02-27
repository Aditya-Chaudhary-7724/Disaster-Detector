"""Satellite image predictor.

Uses TensorFlow/Keras CNN when available.
Falls back to a deterministic lightweight heuristic when TensorFlow is unavailable.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent
SAT_DATASET_DIR = ROOT / "dataset"
MODEL_PATH = ROOT / "models" / "satellite_model.h5"
IMG_SIZE = (64, 64)

_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
_MODEL_CACHE = None
_BACKEND = "heuristic"


def _tf_available():
    try:
        import tensorflow as tf  # noqa: F401

        return True
    except Exception:
        return False


def _ensure_placeholder_dataset(disaster_type: str | None = None) -> None:
    hazards = ["earthquake", "flood", "landslide"] if not disaster_type else [disaster_type]

    for hz in hazards:
        for label in ["safe", "pre_disaster"]:
            d = SAT_DATASET_DIR / hz / label
            d.mkdir(parents=True, exist_ok=True)

            existing = [p for p in d.iterdir() if p.suffix.lower() in _EXTS]
            if existing:
                continue

            rng = np.random.default_rng(abs(hash(f"{hz}:{label}")) % (2**32))
            for i in range(8):
                arr = np.zeros((IMG_SIZE[0], IMG_SIZE[1], 3), dtype=np.uint8)
                base = rng.integers(40, 170)
                arr[:, :, :] = base

                if label == "pre_disaster":
                    for _ in range(18):
                        x1, y1 = rng.integers(0, IMG_SIZE[0], size=2)
                        x2, y2 = rng.integers(0, IMG_SIZE[0], size=2)
                        arr[min(x1, x2) : max(x1, x2) + 1, min(y1, y2) : max(y1, y2) + 1, rng.integers(0, 3)] = rng.integers(170, 255)
                else:
                    arr = np.clip(arr + rng.normal(0, 8, arr.shape), 0, 255).astype(np.uint8)

                Image.fromarray(arr).save(d / f"placeholder_{i}.png")


def _load_image(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB").resize(IMG_SIZE)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr


def _latest_image_for_disaster(disaster_type: str) -> Optional[Path]:
    base = SAT_DATASET_DIR / disaster_type
    if not base.exists():
        return None

    files = [p for p in base.rglob("*") if p.suffix.lower() in _EXTS and p.is_file()]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def _heuristic_probability(arr: np.ndarray) -> float:
    gray = arr.mean(axis=2)
    contrast = float(gray.std())
    edges = float(np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean())
    p = (0.55 * contrast + 0.45 * edges) * 2.2
    return float(np.clip(p, 0.0, 1.0))


def _load_tf_model_once():
    global _MODEL_CACHE, _BACKEND
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if not _tf_available() or not MODEL_PATH.exists():
        _BACKEND = "heuristic"
        _MODEL_CACHE = None
        return None

    import tensorflow as tf

    _MODEL_CACHE = tf.keras.models.load_model(MODEL_PATH)
    _BACKEND = "tensorflow"
    return _MODEL_CACHE


def preload_satellite_model() -> Dict[str, object]:
    model = _load_tf_model_once()
    return {
        "loaded": bool(model is not None),
        "backend": _BACKEND,
        "model_path": str(MODEL_PATH),
    }


def train_satellite_model(disaster_type: str | None = None, epochs: int = 3) -> Dict[str, object]:
    _ensure_placeholder_dataset(disaster_type)

    if not _tf_available():
        return {
            "success": False,
            "backend": "heuristic",
            "message": "TensorFlow not installed. Placeholder dataset prepared; heuristic mode active.",
            "model_path": str(MODEL_PATH),
        }

    import tensorflow as tf

    hazards = ["earthquake", "flood", "landslide"] if not disaster_type else [disaster_type]
    X: List[np.ndarray] = []
    y: List[int] = []

    for hz in hazards:
        for label, target in [("safe", 0), ("pre_disaster", 1)]:
            d = SAT_DATASET_DIR / hz / label
            for p in d.rglob("*"):
                if p.suffix.lower() not in _EXTS or not p.is_file():
                    continue
                try:
                    X.append(_load_image(p))
                    y.append(target)
                except Exception:
                    continue

    if len(X) < 10:
        return {"success": False, "error": "Insufficient satellite images for training"}

    X_arr = np.asarray(X, dtype=np.float32)
    y_arr = np.asarray(y, dtype=np.float32)

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3)),
            tf.keras.layers.Conv2D(16, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(32, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation="relu"),
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

    model.fit(X_arr, y_arr, epochs=max(1, int(epochs)), batch_size=16, verbose=0)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)

    global _MODEL_CACHE, _BACKEND
    _MODEL_CACHE = model
    _BACKEND = "tensorflow"

    return {
        "success": True,
        "backend": "tensorflow",
        "samples": int(len(X_arr)),
        "model_path": str(MODEL_PATH),
    }


def _predict_sync(disaster_type: str, image_path: Optional[str] = None) -> Dict[str, object]:
    disaster_type = (disaster_type or "").lower().strip()
    if disaster_type not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type"}

    _ensure_placeholder_dataset(disaster_type)

    chosen: Optional[Path] = None
    if image_path:
        p = Path(image_path)
        if p.exists() and p.suffix.lower() in _EXTS:
            chosen = p
    if chosen is None:
        chosen = _latest_image_for_disaster(disaster_type)

    if chosen is None:
        return {"success": False, "error": "No satellite image available"}

    arr = _load_image(chosen)

    model = _load_tf_model_once()
    if model is not None:
        pred = float(model.predict(np.expand_dims(arr, axis=0), verbose=0)[0][0])
        backend = "tensorflow"
    else:
        pred = _heuristic_probability(arr)
        backend = "heuristic"

    pred = float(np.clip(pred, 0.0, 1.0))
    level = "High" if pred >= 0.75 else "Medium" if pred >= 0.40 else "Low"

    return {
        "success": True,
        "disaster": disaster_type,
        "image_used": str(chosen),
        "satellite_score": round(pred, 4),
        "risk_level": level,
        "backend": backend,
    }


def _crop_by_bbox(arr: np.ndarray, bbox: Tuple[float, float, float, float]) -> np.ndarray:
    min_lat, max_lat, min_lon, max_lon = bbox

    # Approximate India bounding extents for pixel mapping.
    lat_lo, lat_hi = 6.0, 38.5
    lon_lo, lon_hi = 67.0, 98.5

    h, w = arr.shape[0], arr.shape[1]

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    x1 = int((clamp(min_lon, lon_lo, lon_hi) - lon_lo) / (lon_hi - lon_lo) * (w - 1))
    x2 = int((clamp(max_lon, lon_lo, lon_hi) - lon_lo) / (lon_hi - lon_lo) * (w - 1))
    y1 = int((lat_hi - clamp(max_lat, lat_lo, lat_hi)) / (lat_hi - lat_lo) * (h - 1))
    y2 = int((lat_hi - clamp(min_lat, lat_lo, lat_hi)) / (lat_hi - lat_lo) * (h - 1))

    x1, x2 = sorted((max(0, x1), min(w - 1, x2)))
    y1, y2 = sorted((max(0, y1), min(h - 1, y2)))

    if x2 <= x1 or y2 <= y1:
        return arr

    cropped = arr[y1 : y2 + 1, x1 : x2 + 1, :]
    if cropped.size == 0:
        return arr
    return np.asarray(Image.fromarray((cropped * 255).astype(np.uint8)).resize(IMG_SIZE), dtype=np.float32) / 255.0


def predict_satellite_risk_for_bbox(disaster_type: str, bbox: Tuple[float, float, float, float], image_path: Optional[str] = None) -> Dict[str, object]:
    disaster_type = (disaster_type or "").lower().strip()
    if disaster_type not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type"}

    _ensure_placeholder_dataset(disaster_type)

    chosen: Optional[Path] = None
    if image_path:
        p = Path(image_path)
        if p.exists() and p.suffix.lower() in _EXTS:
            chosen = p
    if chosen is None:
        chosen = _latest_image_for_disaster(disaster_type)
    if chosen is None:
        return {"success": False, "error": "No satellite image available"}

    full = _load_image(chosen)
    arr = _crop_by_bbox(full, bbox)

    model = _load_tf_model_once()
    if model is not None:
        pred = float(model.predict(np.expand_dims(arr, axis=0), verbose=0)[0][0])
        backend = "tensorflow"
    else:
        pred = _heuristic_probability(arr)
        backend = "heuristic"

    pred = float(np.clip(pred, 0.0, 1.0))
    level = "High" if pred >= 0.75 else "Medium" if pred >= 0.40 else "Low"
    return {
        "success": True,
        "disaster": disaster_type,
        "image_used": str(chosen),
        "satellite_score": round(pred, 4),
        "risk_level": level,
        "backend": backend,
        "bbox": {
            "min_lat": round(float(bbox[0]), 5),
            "max_lat": round(float(bbox[1]), 5),
            "min_lon": round(float(bbox[2]), 5),
            "max_lon": round(float(bbox[3]), 5),
        },
    }


async def predict_satellite_risk_async(disaster_type: str, image_path: Optional[str] = None) -> Dict[str, object]:
    return await asyncio.to_thread(_predict_sync, disaster_type, image_path)


def predict_satellite_risk(disaster_type: str, image_path: Optional[str] = None) -> Dict[str, object]:
    try:
        return asyncio.run(asyncio.wait_for(predict_satellite_risk_async(disaster_type, image_path), timeout=0.35))
    except Exception:
        return _predict_sync(disaster_type, image_path)

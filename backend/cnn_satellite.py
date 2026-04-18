"""Coordinate-aware CNN-style satellite predictor.

The model consumes a static-map image for a real disaster location rather than a
random local sample. TensorFlow/Keras is used when available; otherwise the
predictor falls back to deterministic image heuristics.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import joblib
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
DATASET_DIR = ROOT / "dataset_cnn"
MODEL_DIR = ROOT / "models"
META_PATH = MODEL_DIR / "cnn_satellite_meta.pkl"
IMG_SIZE = (64, 64)
STATIC_SIZE = (512, 512)
_EXTS = {".png", ".jpg", ".jpeg"}
_MODEL_CACHE = None
_META_CACHE: Dict[str, object] | None = None
_BACKEND = "heuristic"


def _tf_available() -> bool:
    try:
        import tensorflow  # noqa: F401

        return True
    except Exception:
        return False


def build_static_map_url(lat: float, lng: float, zoom: int = 11) -> str:
    query = urlencode(
        {
            "center": f"{lat:.5f},{lng:.5f}",
            "zoom": str(zoom),
            "size": f"{STATIC_SIZE[0]}x{STATIC_SIZE[1]}",
            "maptype": "mapnik",
            "markers": f"{lat:.5f},{lng:.5f},red-pushpin",
        }
    )
    return f"https://staticmap.openstreetmap.de/staticmap.php?{query}"


def _make_pattern_image(category: str, idx: int) -> Image.Image:
    rng = np.random.default_rng(abs(hash(f"{category}:{idx}")) % (2**32))
    arr = np.zeros((IMG_SIZE[0], IMG_SIZE[1], 3), dtype=np.uint8)

    base_colors = {
        "flood": (32, 88, 160),
        "no_flood": (74, 124, 78),
        "landslide": (124, 82, 56),
        "no_landslide": (86, 140, 94),
    }
    arr[:, :, :] = base_colors.get(category, (90, 90, 90))
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    if category == "flood":
        for _ in range(6):
            y = int(rng.integers(0, IMG_SIZE[1]))
            draw.rectangle([0, y, IMG_SIZE[0], min(IMG_SIZE[1], y + int(rng.integers(5, 11)))], fill=(36, 112, 214))
    elif category == "landslide":
        for _ in range(6):
            x1 = int(rng.integers(0, IMG_SIZE[0] // 2))
            y1 = int(rng.integers(0, IMG_SIZE[1] // 2))
            x2 = x1 + int(rng.integers(18, 42))
            y2 = y1 + int(rng.integers(10, 28))
            draw.polygon([(x1, y1), (x2, y1 + 4), (x1 + 8, y2)], fill=(166, 104, 54))
    elif category == "no_flood":
        for _ in range(8):
            x = int(rng.integers(0, IMG_SIZE[0]))
            y = int(rng.integers(0, IMG_SIZE[1]))
            draw.ellipse([x, y, x + 10, y + 10], fill=(52, 148, 84))
    else:
        for _ in range(7):
            x = int(rng.integers(0, IMG_SIZE[0] - 12))
            y = int(rng.integers(0, IMG_SIZE[1] - 12))
            draw.rectangle([x, y, x + 10, y + 8], fill=(94, 156, 106))

    return img


def ensure_cnn_dataset() -> None:
    for category in ["flood", "no_flood", "landslide", "no_landslide"]:
        folder = DATASET_DIR / category
        folder.mkdir(parents=True, exist_ok=True)
        existing = [p for p in folder.iterdir() if p.suffix.lower() in _EXTS]
        if existing:
            continue
        for idx in range(10):
            _make_pattern_image(category, idx).save(folder / f"{category}_{idx}.png")


def _load_image(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB").resize(IMG_SIZE)
    return np.asarray(img, dtype=np.float32) / 255.0


def _fetch_static_map_image(lat: float, lng: float, zoom: int = 11) -> tuple[np.ndarray, str, str]:
    url = build_static_map_url(lat, lng, zoom=zoom)
    headers = {"User-Agent": "DisasterDetector/1.0"}
    try:
        with urlopen(Request(url, headers=headers), timeout=4) as response:
            img = Image.open(BytesIO(response.read())).convert("RGB").resize(IMG_SIZE)
            return np.asarray(img, dtype=np.float32) / 255.0, url, "static-map"
    except (URLError, OSError, ValueError):
        pass

    img = Image.new("RGB", STATIC_SIZE, color=(95, 138, 88))
    draw = ImageDraw.Draw(img)
    for offset in range(0, STATIC_SIZE[0], 48):
        draw.line((offset, 0, offset, STATIC_SIZE[1]), fill=(216, 214, 196), width=3)
    for offset in range(0, STATIC_SIZE[1], 52):
        draw.line((0, offset, STATIC_SIZE[0], offset), fill=(70, 102, 67), width=2)
    marker_x = int(STATIC_SIZE[0] / 2)
    marker_y = int(STATIC_SIZE[1] / 2)
    draw.ellipse((marker_x - 18, marker_y - 18, marker_x + 18, marker_y + 18), fill=(210, 52, 52))
    draw.ellipse((marker_x - 28, marker_y - 28, marker_x + 28, marker_y + 28), outline=(255, 244, 214), width=4)
    img = img.resize(IMG_SIZE)
    return np.asarray(img, dtype=np.float32) / 255.0, url, "synthetic-map-fallback"


def _heuristic_predict(arr: np.ndarray, disaster_hint: str = "", weather: Optional[Dict[str, object]] = None) -> Dict[str, float]:
    blue = float(arr[:, :, 2].mean())
    green = float(arr[:, :, 1].mean())
    red = float(arr[:, :, 0].mean())
    contrast = float(arr.std())
    flood_prob = float(np.clip(0.72 * blue + 0.22 * contrast - 0.30 * green, 0, 1))
    landslide_prob = float(np.clip(0.66 * red + 0.30 * contrast - 0.18 * green, 0, 1))
    if weather:
        rainfall = float(weather.get("rainfall_mm") or 0.0)
        humidity = float(weather.get("humidity") or 70.0)
        wind = float(weather.get("wind_speed_mps") or 0.0)
        flood_prob = float(np.clip(flood_prob + 0.10 * min(rainfall / 20.0, 1.0) + 0.05 * min(humidity / 100.0, 1.0), 0, 1))
        landslide_prob = float(np.clip(landslide_prob + 0.08 * min(rainfall / 20.0, 1.0) + 0.04 * min(wind / 12.0, 1.0), 0, 1))
    if disaster_hint == "flood":
        flood_prob = float(np.clip(flood_prob + 0.08, 0, 1))
    elif disaster_hint == "landslide":
        landslide_prob = float(np.clip(landslide_prob + 0.08, 0, 1))
    confidence = float(np.clip(max(flood_prob, landslide_prob) * 0.82 + abs(flood_prob - landslide_prob) * 0.18, 0, 1))
    return {
        "flood_prob": round(flood_prob, 4),
        "landslide_prob": round(landslide_prob, 4),
        "confidence": round(confidence, 4),
    }


def _load_or_train_model():
    global _MODEL_CACHE, _META_CACHE, _BACKEND
    if _META_CACHE is not None:
        return _MODEL_CACHE, _META_CACHE

    ensure_cnn_dataset()

    if not _tf_available():
        _BACKEND = "heuristic"
        _META_CACHE = {"backend": _BACKEND, "accuracy": None, "samples": 40}
        return None, _META_CACHE

    import tensorflow as tf

    model_path = MODEL_DIR / "cnn_satellite.keras"
    if model_path.exists() and META_PATH.exists():
        _MODEL_CACHE = tf.keras.models.load_model(model_path)
        _META_CACHE = joblib.load(META_PATH)
        _BACKEND = "tensorflow"
        return _MODEL_CACHE, _META_CACHE

    X: List[np.ndarray] = []
    y_flood: List[int] = []
    y_landslide: List[int] = []
    for category in ["flood", "no_flood", "landslide", "no_landslide"]:
        for img_path in (DATASET_DIR / category).iterdir():
            if img_path.suffix.lower() not in _EXTS:
                continue
            X.append(_load_image(img_path))
            y_flood.append(1 if category == "flood" else 0)
            y_landslide.append(1 if category == "landslide" else 0)

    X_arr = np.asarray(X, dtype=np.float32)
    y_arr = np.asarray(list(zip(y_flood, y_landslide)), dtype=np.float32)

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3)),
            tf.keras.layers.Conv2D(16, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(32, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(48, 3, activation="relu"),
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(2, activation="sigmoid"),
        ]
    )
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    model.fit(X_arr, y_arr, epochs=6, batch_size=8, verbose=0)

    preds = model.predict(X_arr, verbose=0)
    flood_acc = float(((preds[:, 0] > 0.5) == np.asarray(y_flood)).mean())
    landslide_acc = float(((preds[:, 1] > 0.5) == np.asarray(y_landslide)).mean())
    meta = {
        "backend": "tensorflow",
        "accuracy": round((flood_acc + landslide_acc) / 2.0, 4),
        "samples": int(len(X_arr)),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(model_path)
    joblib.dump(meta, META_PATH)
    _MODEL_CACHE = model
    _META_CACHE = meta
    _BACKEND = "tensorflow"
    return model, meta


def predict_from_coordinates(lat: float, lng: float, disaster: str = "", zoom: int = 11, weather: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    model, meta = _load_or_train_model()
    arr, image_url, image_source = _fetch_static_map_image(lat, lng, zoom=zoom)

    if model is None:
        probs = _heuristic_predict(arr, disaster_hint=disaster, weather=weather)
    else:
        pred = model.predict(np.expand_dims(arr, axis=0), verbose=0)[0]
        flood_prob = float(np.clip(pred[0], 0, 1))
        landslide_prob = float(np.clip(pred[1], 0, 1))
        if weather:
            rainfall = float(weather.get("rainfall_mm") or 0.0)
            humidity = float(weather.get("humidity") or 70.0)
            wind = float(weather.get("wind_speed_mps") or 0.0)
            flood_prob = float(np.clip(flood_prob + 0.08 * min(rainfall / 20.0, 1.0) + 0.04 * min(humidity / 100.0, 1.0), 0, 1))
            landslide_prob = float(np.clip(landslide_prob + 0.06 * min(rainfall / 20.0, 1.0) + 0.04 * min(wind / 12.0, 1.0), 0, 1))
        if disaster == "flood":
            flood_prob = float(np.clip(flood_prob + 0.05, 0, 1))
        elif disaster == "landslide":
            landslide_prob = float(np.clip(landslide_prob + 0.05, 0, 1))
        probs = {
            "flood_prob": round(flood_prob, 4),
            "landslide_prob": round(landslide_prob, 4),
            "confidence": round(max(flood_prob, landslide_prob), 4),
        }

    similarity = max(float(probs["flood_prob"]), float(probs["landslide_prob"]))
    return {
        "success": True,
        **probs,
        "backend": _BACKEND,
        "model_accuracy": meta.get("accuracy"),
        "image_url": image_url,
        "image_source": image_source,
        "lat": round(float(lat), 5),
        "lng": round(float(lng), 5),
        "disaster": disaster,
        "similarity": round(similarity, 4),
        "weather_used": weather or {},
    }


def predict_from_image(image_path: str) -> Dict[str, object]:
    path = Path(image_path)
    if not path.exists():
        return {"success": False, "error": "Image not found"}
    arr = _load_image(path)
    model, meta = _load_or_train_model()
    if model is None:
        probs = _heuristic_predict(arr)
    else:
        pred = model.predict(np.expand_dims(arr, axis=0), verbose=0)[0]
        probs = {
            "flood_prob": round(float(np.clip(pred[0], 0, 1)), 4),
            "landslide_prob": round(float(np.clip(pred[1], 0, 1)), 4),
            "confidence": round(float(np.max(pred)), 4),
        }
    return {
        "success": True,
        **probs,
        "image_path": str(path),
        "backend": _BACKEND,
        "model_accuracy": meta.get("accuracy"),
    }


def run_auto_cnn_prediction(lat: Optional[float] = None, lng: Optional[float] = None, disaster: str = "", weather: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    if lat is None or lng is None:
        return {"success": False, "error": "Coordinates are required for geospatial CNN prediction"}
    return predict_from_coordinates(lat=float(lat), lng=float(lng), disaster=disaster, weather=weather)


def get_cnn_model_info() -> Dict[str, object]:
    _, meta = _load_or_train_model()
    return meta

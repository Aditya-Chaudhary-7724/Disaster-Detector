"""Generate a large, balanced multi-hazard dataset for ML experiments.

Outputs:
- backend/datasets/disaster_dataset.csv   (primary training dataset)
- backend/datasets/multi_hazard_dataset.csv (compatibility copy)

Design goals:
- >= 20,000 rows
- Balanced risk classes: Low, Medium, High
- Physically plausible India-focused values
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

PRIMARY_OUTPUT = Path(__file__).parent / "datasets" / "disaster_dataset.csv"
COMPAT_OUTPUT = Path(__file__).parent / "datasets" / "multi_hazard_dataset.csv"
SEED = 2026
TOTAL_ROWS = 21000


@dataclass(frozen=True)
class Region:
    place: str
    lat: float
    lon: float


EARTHQUAKE_REGIONS = [
    Region("Kutch, Gujarat", 23.25, 69.67),
    Region("Kangra, Himachal Pradesh", 32.10, 76.27),
    Region("Tezpur, Assam", 26.64, 92.80),
    Region("Gangtok, Sikkim", 27.33, 88.61),
    Region("Andaman", 11.67, 92.75),
]

FLOOD_REGIONS = [
    Region("Guwahati, Assam", 26.14, 91.74),
    Region("Patna, Bihar", 25.61, 85.14),
    Region("Kolkata Delta", 22.57, 88.36),
    Region("Kerala Midlands", 10.85, 76.27),
    Region("Siliguri, WB", 26.73, 88.39),
]

LANDSLIDE_REGIONS = [
    Region("Shimla, Himachal Pradesh", 31.10, 77.17),
    Region("Nainital, Uttarakhand", 29.38, 79.46),
    Region("Darjeeling Hills", 27.04, 88.26),
    Region("Shillong Plateau", 25.58, 91.89),
    Region("Nilgiris", 11.40, 76.70),
]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def jitter(region: Region, rng: random.Random) -> tuple[float, float]:
    return round(region.lat + rng.uniform(-0.45, 0.45), 5), round(region.lon + rng.uniform(-0.45, 0.45), 5)


def _sample_for(disaster: str, risk: str, rng: random.Random) -> Dict[str, float]:
    # Risk-targeted sampling keeps class balance realistic while preserving physical relations.
    if disaster == "earthquake":
        region = rng.choice(EARTHQUAKE_REGIONS)
        lat, lon = jitter(region, rng)

        if risk == "High":
            seismic = rng.uniform(6.0, 7.9)
            depth = rng.uniform(4.0, 25.0)
        elif risk == "Medium":
            seismic = rng.uniform(4.5, 6.1)
            depth = rng.uniform(12.0, 80.0)
        else:
            seismic = rng.uniform(2.8, 4.8)
            depth = rng.uniform(35.0, 220.0)

        rainfall = rng.uniform(0, 120)
        soil = rng.uniform(0.25, 0.75)
        slope = rng.uniform(3, 38)
        ndvi = rng.uniform(0.2, 0.8)

    elif disaster == "flood":
        region = rng.choice(FLOOD_REGIONS)
        lat, lon = jitter(region, rng)

        if risk == "High":
            rainfall = rng.uniform(170, 340)
            soil = rng.uniform(0.75, 0.98)
            slope = rng.uniform(0.5, 9.0)  # flatter terrain -> flood accumulation
        elif risk == "Medium":
            rainfall = rng.uniform(90, 200)
            soil = rng.uniform(0.55, 0.85)
            slope = rng.uniform(1.5, 16)
        else:
            rainfall = rng.uniform(5, 110)
            soil = rng.uniform(0.2, 0.65)
            slope = rng.uniform(4, 24)

        seismic = rng.uniform(0.0, 3.5)
        depth = rng.uniform(25, 200)
        ndvi = rng.uniform(0.2, 0.85)

    else:  # landslide
        region = rng.choice(LANDSLIDE_REGIONS)
        lat, lon = jitter(region, rng)

        if risk == "High":
            rainfall = rng.uniform(120, 300)
            slope = rng.uniform(35, 60)
            soil = rng.uniform(0.7, 0.98)
            ndvi = rng.uniform(0.12, 0.45)
        elif risk == "Medium":
            rainfall = rng.uniform(70, 180)
            slope = rng.uniform(20, 45)
            soil = rng.uniform(0.5, 0.82)
            ndvi = rng.uniform(0.2, 0.65)
        else:
            rainfall = rng.uniform(10, 120)
            slope = rng.uniform(8, 30)
            soil = rng.uniform(0.2, 0.65)
            ndvi = rng.uniform(0.35, 0.9)

        seismic = rng.uniform(0.0, 5.8)
        depth = rng.uniform(8, 120)

    plant_density = clamp(0.14 + 0.78 * ndvi + rng.uniform(-0.12, 0.12), 0.05, 0.99)

    return {
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "rainfall_24h_mm": round(rainfall, 2),
        "soil_moisture": round(soil, 3),
        "slope_deg": round(slope, 2),
        "ndvi": round(ndvi, 3),
        "plant_density": round(plant_density, 3),
        "seismic_magnitude": round(seismic, 2),
        "seismic_mag": round(seismic, 2),
        "depth_km": round(depth, 2),
    }


def generate_dataset(total_rows: int = TOTAL_ROWS, seed: int = SEED) -> None:
    rng = random.Random(seed)
    PRIMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    risk_levels = ["Low", "Medium", "High"]
    disasters = ["earthquake", "flood", "landslide"]

    per_risk = total_rows // len(risk_levels)
    rows: List[Dict[str, object]] = []
    t0 = datetime.utcnow() - timedelta(days=365)

    for i, risk in enumerate(risk_levels):
        for j in range(per_risk):
            disaster = disasters[(j + i) % len(disasters)]
            features = _sample_for(disaster, risk, rng)
            ts = (t0 + timedelta(minutes=30 * (i * per_risk + j))).strftime("%Y-%m-%d %H:%M:%S")

            rows.append(
                {
                    "timestamp": ts,
                    "disaster_type": disaster,
                    **features,
                    "risk_label": risk,
                }
            )

    # Fill remainder if total_rows not divisible by 3
    while len(rows) < total_rows:
        risk = rng.choice(risk_levels)
        disaster = rng.choice(disasters)
        features = _sample_for(disaster, risk, rng)
        ts = (t0 + timedelta(minutes=30 * len(rows))).strftime("%Y-%m-%d %H:%M:%S")
        rows.append({"timestamp": ts, "disaster_type": disaster, **features, "risk_label": risk})

    # Controlled stochastic label noise to avoid unrealistically perfect class separation.
    # This makes evaluation closer to real operational data conditions.
    noise_rate = 0.08
    for row in rows:
        if rng.random() < noise_rate:
            current = row["risk_label"]
            row["risk_label"] = rng.choice([x for x in risk_levels if x != current])

    rng.shuffle(rows)

    fieldnames = [
        "timestamp",
        "disaster_type",
        "latitude",
        "longitude",
        "rainfall_24h_mm",
        "soil_moisture",
        "slope_deg",
        "ndvi",
        "plant_density",
        "seismic_magnitude",
        "seismic_mag",
        "depth_km",
        "risk_label",
    ]

    for output in (PRIMARY_OUTPUT, COMPAT_OUTPUT):
        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(f"Generated {len(rows)} rows")
    print(f"Primary dataset: {PRIMARY_OUTPUT}")
    print(f"Compatibility copy: {COMPAT_OUTPUT}")


if __name__ == "__main__":
    generate_dataset()

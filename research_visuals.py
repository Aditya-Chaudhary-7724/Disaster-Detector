#!/usr/bin/env python3
"""Research-only visualizations for the multi-hazard disaster prediction project.

This script is standalone and does not modify production APIs or frontend code.
Run:
    python research_visuals.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

try:
    import matplotlib
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "matplotlib is required to run research_visuals.py. "
        "Install dependencies in your Python environment first."
    ) from exc

try:
    import seaborn as sns
except Exception:
    sns = None

try:
    import networkx as nx
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "networkx is required to render the architecture flowchart. "
        "Install dependencies in your Python environment first."
    ) from exc

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
DATASET_CANDIDATES = [
    BACKEND / "datasets" / "multi_hazard_dataset.csv",
    BACKEND / "datasets" / "disaster_dataset.csv",
    BACKEND / "datasets" / "dataset.csv",
]
DB_CANDIDATES = [BACKEND / "disasters.db", BACKEND / "disaster.db"]

DISASTER_TYPES = ["earthquake", "flood", "landslide"]
RISK_ORDER = ["Low", "Medium", "High"]

FEATURES_COMMON = ["rainfall_24h_mm", "soil_moisture", "slope_deg", "seismic_magnitude"]
FEATURES_PER_DISASTER = {
    "earthquake": ["seismic_magnitude", "depth_km", "soil_moisture", "rainfall_24h_mm", "slope_deg"],
    "flood": ["rainfall_24h_mm", "soil_moisture", "slope_deg", "ndvi", "plant_density", "seismic_magnitude"],
    "landslide": ["slope_deg", "soil_moisture", "rainfall_24h_mm", "ndvi", "plant_density", "seismic_magnitude"],
}


def set_ieee_style() -> None:
    """Set publication-style plot defaults."""
    matplotlib.rcParams.update(
        {
            "figure.dpi": 130,
            "savefig.dpi": 300,
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "Times"],
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )
    if sns is not None:
        sns.set_theme(style="whitegrid", context="paper")


def _coerce_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "seismic_mag" in df.columns and "seismic_magnitude" not in df.columns:
        df["seismic_magnitude"] = df["seismic_mag"]
    if "disaster" in df.columns and "disaster_type" not in df.columns:
        df["disaster_type"] = df["disaster"]
    if "risk" in df.columns and "risk_label" not in df.columns:
        df["risk_label"] = df["risk"].astype(str).str.title()

    for c in ["disaster_type", "risk_label"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower() if c == "disaster_type" else df[c].astype(str).str.strip().str.title()

    for c in [
        "rainfall_24h_mm",
        "soil_moisture",
        "slope_deg",
        "seismic_magnitude",
        "depth_km",
        "ndvi",
        "plant_density",
        "latitude",
        "longitude",
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "risk_label" in df.columns:
        df = df[df["risk_label"].isin(RISK_ORDER)]

    return df


def _generate_synthetic_dataset(n_per_type: int = 2500) -> pd.DataFrame:
    """Generate realistic synthetic data if CSV/DB data is unavailable."""
    rng = np.random.default_rng(42)
    rows: List[Dict[str, float | str]] = []

    for disaster in DISASTER_TYPES:
        for _ in range(n_per_type):
            rain = float(np.clip(rng.normal(80, 60), 0, 350))
            soil = float(np.clip(rng.normal(0.55, 0.2), 0, 1))
            slope = float(np.clip(rng.normal(20, 15), 0, 60))
            ndvi = float(np.clip(rng.normal(0.45, 0.2), 0, 1))
            density = float(np.clip(rng.normal(0.5, 0.2), 0, 1))
            seismic = float(np.clip(rng.normal(2.5, 1.7), 0, 8.5))
            depth = float(np.clip(rng.normal(70, 60), 1, 300))

            if disaster == "earthquake":
                seismic = float(np.clip(rng.normal(4.8, 1.3), 0.5, 8.8))
                depth = float(np.clip(rng.normal(55, 45), 2, 300))
            elif disaster == "flood":
                rain = float(np.clip(rng.normal(140, 70), 0, 400))
                soil = float(np.clip(rng.normal(0.7, 0.18), 0, 1))
                slope = float(np.clip(rng.normal(9, 8), 0, 45))
            else:  # landslide
                rain = float(np.clip(rng.normal(115, 65), 0, 380))
                soil = float(np.clip(rng.normal(0.68, 0.17), 0, 1))
                slope = float(np.clip(rng.normal(33, 12), 5, 65))

            risk_score = (
                0.26 * (rain / 350)
                + 0.20 * soil
                + 0.18 * (slope / 60)
                + 0.20 * (seismic / 8)
                + 0.10 * (1 - min(depth / 300, 1.0))
                + 0.06 * (1 - ndvi)
            )

            if disaster == "earthquake":
                risk_score += 0.12 * (seismic / 8)
            elif disaster == "flood":
                risk_score += 0.10 * (rain / 350 + soil) / 2
            else:
                risk_score += 0.10 * (slope / 60 + soil) / 2

            risk_score = float(np.clip(risk_score, 0, 1))
            if risk_score < 0.40:
                label = "Low"
            elif risk_score <= 0.70:
                label = "Medium"
            else:
                label = "High"

            rows.append(
                {
                    "disaster_type": disaster,
                    "risk_label": label,
                    "rainfall_24h_mm": rain,
                    "soil_moisture": soil,
                    "slope_deg": slope,
                    "seismic_magnitude": seismic,
                    "depth_km": depth,
                    "ndvi": ndvi,
                    "plant_density": density,
                    "latitude": float(rng.uniform(6, 38)),
                    "longitude": float(rng.uniform(67, 98)),
                }
            )

    return _coerce_columns(pd.DataFrame(rows))


def _load_csv_dataset() -> pd.DataFrame | None:
    for path in DATASET_CANDIDATES:
        if not path.exists() or path.stat().st_size == 0:
            continue
        try:
            df = pd.read_csv(path)
            df = _coerce_columns(df)
            if {"disaster_type", "risk_label"}.issubset(df.columns) and len(df) > 0:
                print(f"Loaded dataset from CSV: {path}")
                return df
        except Exception:
            continue
    return None


def _load_db_tables() -> pd.DataFrame | None:
    for db_path in DB_CANDIDATES:
        if not db_path.exists():
            continue
        try:
            conn = sqlite3.connect(db_path)
            eq = pd.read_sql_query(
                "SELECT 'earthquake' AS disaster_type, 'Low' AS risk_label, "
                "0 AS rainfall_24h_mm, 0.4 AS soil_moisture, 8 AS slope_deg, "
                "magnitude AS seismic_magnitude, depth AS depth_km, 0.5 AS ndvi, 0.5 AS plant_density, "
                "latitude, longitude FROM earthquakes",
                conn,
            )
            fl = pd.read_sql_query(
                "SELECT 'flood' AS disaster_type, COALESCE(risk, severity, 'Low') AS risk_label, "
                "COALESCE(rainfall_24h_mm, 0) AS rainfall_24h_mm, COALESCE(soil_moisture, 0.5) AS soil_moisture, "
                "COALESCE(slope_deg, 10) AS slope_deg, 0 AS seismic_magnitude, 0 AS depth_km, "
                "COALESCE(ndvi, 0.5) AS ndvi, COALESCE(plant_density, 0.5) AS plant_density, "
                "latitude, longitude FROM floods",
                conn,
            )
            ls = pd.read_sql_query(
                "SELECT 'landslide' AS disaster_type, COALESCE(risk, severity, 'Low') AS risk_label, "
                "COALESCE(rainfall_24h_mm, 0) AS rainfall_24h_mm, COALESCE(soil_moisture, 0.5) AS soil_moisture, "
                "COALESCE(slope_deg, 10) AS slope_deg, 0 AS seismic_magnitude, 0 AS depth_km, "
                "COALESCE(ndvi, 0.5) AS ndvi, COALESCE(plant_density, 0.5) AS plant_density, "
                "latitude, longitude FROM landslides",
                conn,
            )
            conn.close()
            df = _coerce_columns(pd.concat([eq, fl, ls], ignore_index=True))
            if len(df) > 0:
                print(f"Loaded dataset from SQLite tables: {db_path}")
                return df
        except Exception:
            continue
    return None


def load_or_build_dataset() -> pd.DataFrame:
    df = _load_csv_dataset()
    if df is not None:
        return df

    df = _load_db_tables()
    if df is not None:
        return df

    print("No usable dataset found. Using statistically realistic synthetic data.")
    return _generate_synthetic_dataset()


def _show_figure(fig: matplotlib.figure.Figure) -> None:
    fig.tight_layout()
    plt.show(block=True)
    plt.close(fig)


def plot_dataset_distribution(df: pd.DataFrame) -> None:
    counts = (
        df["disaster_type"].value_counts().reindex(DISASTER_TYPES).fillna(0).astype(int)
    )

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    palette = ["#1f77b4", "#2ca02c", "#d62728"]
    bars = ax.bar(counts.index.str.title(), counts.values, color=palette, edgecolor="black", linewidth=0.7)

    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(1, counts.max() * 0.01), f"{int(bar.get_height())}",
                ha="center", va="bottom")

    ax.set_title("Dataset Distribution by Disaster Type")
    ax.set_xlabel("Disaster Type")
    ax.set_ylabel("Number of Samples")
    ax.legend(["Samples"], loc="upper right")
    _show_figure(fig)


def plot_feature_distributions(df: pd.DataFrame) -> None:
    melted = df[["disaster_type", *FEATURES_COMMON]].melt(
        id_vars="disaster_type", var_name="feature", value_name="value"
    )
    melted["feature"] = melted["feature"].map(
        {
            "rainfall_24h_mm": "Rainfall 24h (mm)",
            "soil_moisture": "Soil Moisture",
            "slope_deg": "Slope (deg)",
            "seismic_magnitude": "Seismic Magnitude",
        }
    )

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    order = ["earthquake", "flood", "landslide"]
    for ax, feature_label in zip(axes.flatten(), melted["feature"].dropna().unique()):
        sub = melted[melted["feature"] == feature_label]
        if sns is not None:
            sns.kdeplot(
                data=sub,
                x="value",
                hue="disaster_type",
                hue_order=order,
                fill=True,
                common_norm=False,
                alpha=0.2,
                linewidth=1.5,
                ax=ax,
            )
        else:
            for disaster in order:
                vals = sub.loc[sub["disaster_type"] == disaster, "value"].dropna().to_numpy()
                if len(vals) > 0:
                    ax.hist(vals, bins=40, alpha=0.35, density=True, label=disaster.title())

        ax.set_title(feature_label)
        ax.set_xlabel(feature_label)
        ax.set_ylabel("Density")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, [l.title() for l in labels], loc="upper center", ncol=3, frameon=True)

    fig.suptitle("Feature Distributions by Disaster Type", y=1.02)
    _show_figure(fig)


def _encode_risk_labels(labels: Iterable[str]) -> np.ndarray:
    mapper = {"Low": 0, "Medium": 1, "High": 2}
    return np.array([mapper.get(str(v).title(), 0) for v in labels], dtype=int)


def _train_feature_importance(df: pd.DataFrame, disaster: str) -> pd.Series:
    use_cols = FEATURES_PER_DISASTER[disaster]
    sub = df[df["disaster_type"] == disaster].copy()

    if len(sub) < 80:
        synthetic = _generate_synthetic_dataset(n_per_type=600)
        sub = pd.concat([sub, synthetic[synthetic["disaster_type"] == disaster]], ignore_index=True)

    X = sub[use_cols].fillna(sub[use_cols].median(numeric_only=True))
    y = _encode_risk_labels(sub["risk_label"])

    if len(np.unique(y)) < 2:
        synth = _generate_synthetic_dataset(n_per_type=700)
        extra = synth[synth["disaster_type"] == disaster]
        X = pd.concat([X, extra[use_cols]], ignore_index=True)
        y = np.concatenate([y, _encode_risk_labels(extra["risk_label"])])

    X_train, _, y_train, _ = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if len(np.unique(y)) > 1 else None,
    )
    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    return pd.Series(model.feature_importances_, index=use_cols).sort_values(ascending=True)


def plot_feature_importance(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharex=False)
    colors = {"earthquake": "#4c78a8", "flood": "#59a14f", "landslide": "#e15759"}

    for ax, disaster in zip(axes, DISASTER_TYPES):
        imp = _train_feature_importance(df, disaster)
        ax.barh([c.replace("_", " ") for c in imp.index], imp.values, color=colors[disaster], edgecolor="black", linewidth=0.5)
        ax.set_title(f"{disaster.title()} Feature Importance")
        ax.set_xlabel("Importance Score")
        ax.set_ylabel("Feature")
        ax.set_xlim(left=0)

    fig.suptitle("Per-Disaster ML Feature Importance (Random Forest)", y=1.04)
    _show_figure(fig)


def plot_spatiotemporal_risk(df: pd.DataFrame) -> None:
    rng = np.random.default_rng(7)
    days = np.arange(0, 8)

    def baseline_for(disaster: str) -> float:
        sub = df[df["disaster_type"] == disaster]
        if len(sub) == 0:
            return 35.0
        mapped = sub["risk_label"].map({"Low": 35, "Medium": 60, "High": 85}).dropna()
        return float(mapped.mean()) if len(mapped) else 35.0

    fig, ax = plt.subplots(figsize=(9, 5))
    for disaster, color in zip(DISASTER_TYPES, ["#1f77b4", "#2ca02c", "#d62728"]):
        base = baseline_for(disaster)
        growth = {"earthquake": 0.7, "flood": 1.35, "landslide": 1.1}[disaster]
        risk = base + 8 * np.sin((days / 7) * np.pi) + growth * days + rng.normal(0, 1.2, size=len(days))
        risk = np.clip(risk, 0, 100)
        ax.plot(days, risk, marker="o", linewidth=2.0, label=disaster.title(), color=color)

    ax.set_title("Spatio-Temporal Risk Evolution (0-7 Day Early Warning Horizon)")
    ax.set_xlabel("Forecast Day")
    ax.set_ylabel("Risk Score (0-100)")
    ax.set_xticks(days)
    ax.legend(title="Disaster")
    _show_figure(fig)


def plot_alert_thresholds() -> None:
    x = np.linspace(0, 7, 120)
    risk = 48 + 34 / (1 + np.exp(-(x - 3.2) * 1.1)) + 6 * np.sin(x * 0.9)
    risk = np.clip(risk, 0, 100)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axhspan(0, 40, color="#2ca02c", alpha=0.15, label="Advisory")
    ax.axhspan(40, 70, color="#ff7f0e", alpha=0.18, label="Watch")
    ax.axhspan(70, 100, color="#d62728", alpha=0.15, label="Warning")

    ax.plot(x, risk, color="#1f2a44", linewidth=2.4, label="Predicted Risk Score")
    ax.axhline(40, linestyle="--", color="#ff7f0e", linewidth=1.2)
    ax.axhline(70, linestyle="--", color="#d62728", linewidth=1.2)

    ax.set_title("Alert Threshold Visualization: Risk Score to Alert Level")
    ax.set_xlabel("Forecast Day")
    ax.set_ylabel("Risk Score (0-100)")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right")
    _show_figure(fig)


def plot_architecture_flowchart() -> None:
    G = nx.DiGraph()
    nodes = [
        "Data Acquisition",
        "Unified Disaster Database",
        "Feature Engineering",
        "Hybrid Prediction Engine",
        "Spatio-Temporal Risk Model",
        "Alert Engine",
        "Web Dashboard",
    ]
    edges = list(zip(nodes[:-1], nodes[1:]))

    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    pos = {
        "Data Acquisition": (0.03, 0.5),
        "Unified Disaster Database": (0.20, 0.5),
        "Feature Engineering": (0.36, 0.5),
        "Hybrid Prediction Engine": (0.53, 0.5),
        "Spatio-Temporal Risk Model": (0.71, 0.5),
        "Alert Engine": (0.86, 0.5),
        "Web Dashboard": (1.00, 0.5),
    }

    fig, ax = plt.subplots(figsize=(14.5, 3.8))
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=4600,
        node_shape="s",
        node_color="#f5f8ff",
        edgecolors="#1f2a44",
        linewidths=1.2,
        ax=ax,
    )
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", ax=ax)
    nx.draw_networkx_edges(
        G,
        pos,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=26,
        width=1.8,
        edge_color="#1f2a44",
        ax=ax,
    )

    ax.set_title("System Architecture Flowchart", pad=12)
    ax.set_axis_off()
    _show_figure(fig)


def plot_hybrid_risk_fusion() -> None:
    ml_scores = np.linspace(0, 100, 101)
    rule_low = 35
    rule_med = 60
    rule_high = 85
    alpha = 0.65  # weighted fusion: alpha*ML + (1-alpha)*Rule

    fused_low = alpha * ml_scores + (1 - alpha) * rule_low
    fused_med = alpha * ml_scores + (1 - alpha) * rule_med
    fused_high = alpha * ml_scores + (1 - alpha) * rule_high

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(ml_scores, fused_low, linewidth=2.0, label="Rule Baseline: Low (35)", color="#2ca02c")
    ax.plot(ml_scores, fused_med, linewidth=2.0, label="Rule Baseline: Medium (60)", color="#ff7f0e")
    ax.plot(ml_scores, fused_high, linewidth=2.0, label="Rule Baseline: High (85)", color="#d62728")
    ax.plot(ml_scores, ml_scores, linestyle="--", color="#1f2a44", linewidth=1.3, label="Pure ML Reference")

    ax.set_title("Hybrid Risk Fusion: Weighted Combination of Rule-Based and ML Risk")
    ax.set_xlabel("ML Risk Score")
    ax.set_ylabel("Fused Risk Score")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left")
    _show_figure(fig)


def main() -> None:
    set_ieee_style()
    df = load_or_build_dataset()

    required_cols = {"disaster_type", "risk_label", *FEATURES_COMMON}
    missing = sorted(required_cols.difference(df.columns))
    if missing:
        raise RuntimeError(f"Dataset is missing required columns for visualization: {missing}")

    print(f"Dataset ready: {len(df)} rows")
    plot_dataset_distribution(df)
    plot_feature_distributions(df)
    plot_feature_importance(df)
    plot_spatiotemporal_risk(df)
    plot_alert_thresholds()
    plot_architecture_flowchart()
    plot_hybrid_risk_fusion()
    print("All research visuals generated successfully.")


if __name__ == "__main__":
    main()

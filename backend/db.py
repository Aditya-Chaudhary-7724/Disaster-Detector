import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DISASTER_DB_PATH", BASE_DIR / "disasters.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            rainfall REAL NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            seismic_activity REAL NOT NULL,
            soil_moisture REAL NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            predicted_label INTEGER NOT NULL,
            actual_label INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            risk_score REAL NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def insert_prediction(record: dict) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO predictions (
            region, rainfall, temperature, humidity, seismic_activity, soil_moisture,
            risk_score, risk_level, predicted_label, actual_label, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["region"],
            record["rainfall"],
            record["temperature"],
            record["humidity"],
            record["seismic_activity"],
            record["soil_moisture"],
            record["risk_score"],
            record["risk_level"],
            record["predicted_label"],
            record.get("actual_label"),
            record["created_at"],
        ),
    )
    record["id"] = cur.lastrowid
    conn.commit()
    conn.close()
    return record


def get_predictions(limit: int = 100) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def insert_alert(record: dict) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO alerts (region, risk_score, level, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            record["region"],
            record["risk_score"],
            record["level"],
            record["message"],
            record["created_at"],
        ),
    )
    record["id"] = cur.lastrowid
    conn.commit()
    conn.close()
    return record


def get_alerts(limit: int = 100) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_validation_metrics() -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT predicted_label, actual_label
        FROM predictions
        WHERE actual_label IS NOT NULL
        """
    )
    rows = cur.fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        return {
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
        }

    tp = fp = fn = correct = 0
    for row in rows:
        predicted = int(row["predicted_label"])
        actual = int(row["actual_label"])
        if predicted == actual:
            correct += 1
        if predicted == 1 and actual == 1:
            tp += 1
        elif predicted == 1 and actual == 0:
            fp += 1
        elif predicted == 0 and actual == 1:
            fn += 1

    accuracy = correct / total
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "total_predictions": total,
        "correct_predictions": correct,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
    }

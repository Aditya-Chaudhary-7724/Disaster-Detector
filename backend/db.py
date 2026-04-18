import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable

BASE_DIR = Path(__file__).resolve().parent
PRIMARY_DB_PATH = BASE_DIR / "disasters.db"
LEGACY_DB_PATH = BASE_DIR / "disaster.db"


def _resolve_db_path() -> Path:
    env_path = os.getenv("DISASTER_DB_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    if PRIMARY_DB_PATH.exists():
        return PRIMARY_DB_PATH
    if LEGACY_DB_PATH.exists():
        return LEGACY_DB_PATH
    return PRIMARY_DB_PATH


DB_PATH = _resolve_db_path()


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _ensure_columns(conn: sqlite3.Connection, table_name: str, columns: Dict[str, str]) -> None:
    existing = _table_columns(conn, table_name)
    cur = conn.cursor()
    for column_name, column_type in columns.items():
        if column_name not in existing:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _copy_rows_if_empty(target_conn: sqlite3.Connection, source_path: Path, table_name: str) -> None:
    if not source_path.exists() or source_path.resolve() == DB_PATH.resolve():
        return

    cur = target_conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    target_count = int(cur.fetchone()[0])
    if target_count > 0:
        return

    with sqlite3.connect(source_path) as source_conn:
        source_conn.row_factory = sqlite3.Row
        try:
            rows = source_conn.execute(f"SELECT * FROM {table_name}").fetchall()
        except sqlite3.Error:
            return
        if not rows:
            return

        source_columns = [key for key in rows[0].keys()]
        target_columns = list(_table_columns(target_conn, table_name))
        shared_columns = [column for column in source_columns if column in target_columns]
        if not shared_columns:
            return

        placeholders = ", ".join(["?"] * len(shared_columns))
        col_sql = ", ".join(shared_columns)
        values: Iterable[tuple[Any, ...]] = [tuple(row[column] for column in shared_columns) for row in rows]
        cur.executemany(
            f"INSERT OR IGNORE INTO {table_name} ({col_sql}) VALUES ({placeholders})",
            values,
        )


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS earthquakes (
            id TEXT PRIMARY KEY,
            place TEXT,
            magnitude REAL,
            time INTEGER,
            latitude REAL,
            longitude REAL,
            depth REAL,
            last_updated INTEGER
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS floods (
            id TEXT PRIMARY KEY,
            location TEXT,
            place TEXT,
            severity TEXT,
            time INTEGER,
            latitude REAL,
            longitude REAL,
            details TEXT,
            risk TEXT,
            rainfall_24h_mm REAL,
            soil_moisture REAL,
            slope_deg REAL,
            ndvi REAL,
            plant_density REAL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS landslides (
            id TEXT PRIMARY KEY,
            location TEXT,
            place TEXT,
            severity TEXT,
            time INTEGER,
            latitude REAL,
            longitude REAL,
            details TEXT,
            risk TEXT,
            rainfall_24h_mm REAL,
            soil_moisture REAL,
            slope_deg REAL,
            ndvi REAL,
            plant_density REAL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            level TEXT,
            message TEXT,
            lat REAL,
            lon REAL,
            created_at INTEGER,
            alert_type TEXT,
            disaster TEXT,
            region TEXT,
            confidence REAL,
            risk_score REAL,
            timestamp TEXT,
            location TEXT,
            priority TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    _ensure_columns(
        conn,
        "floods",
        {
            "location": "TEXT",
            "place": "TEXT",
            "details": "TEXT",
            "risk": "TEXT",
            "rainfall_24h_mm": "REAL",
            "soil_moisture": "REAL",
            "slope_deg": "REAL",
            "ndvi": "REAL",
            "plant_density": "REAL",
        },
    )
    _ensure_columns(
        conn,
        "landslides",
        {
            "location": "TEXT",
            "place": "TEXT",
            "details": "TEXT",
            "risk": "TEXT",
            "rainfall_24h_mm": "REAL",
            "soil_moisture": "REAL",
            "slope_deg": "REAL",
            "ndvi": "REAL",
            "plant_density": "REAL",
        },
    )
    _ensure_columns(conn, "earthquakes", {"last_updated": "INTEGER"})
    _ensure_columns(
        conn,
        "alerts",
        {
            "alert_type": "TEXT",
            "disaster": "TEXT",
            "region": "TEXT",
            "confidence": "REAL",
            "risk_score": "REAL",
            "timestamp": "TEXT",
            "location": "TEXT",
            "priority": "TEXT",
        },
    )

    for table_name in ["earthquakes", "floods", "landslides", "alerts", "sync_state"]:
        _copy_rows_if_empty(conn, LEGACY_DB_PATH if DB_PATH == PRIMARY_DB_PATH else PRIMARY_DB_PATH, table_name)

    conn.commit()
    conn.close()
    print(f"DB PATH: {DB_PATH}")


def insert_earthquake(q: Dict[str, Any]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO earthquakes
            (id, place, magnitude, time, latitude, longitude, depth, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                q["id"],
                q["place"],
                q["magnitude"],
                q["time"],
                q["latitude"],
                q["longitude"],
                q["depth"],
                q.get("last_updated"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_earthquakes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, place, magnitude, depth, time, latitude, longitude
        FROM earthquakes
        ORDER BY time DESC
        LIMIT 50
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "place": r[1],
            "magnitude": r[2],
            "depth": r[3],
            "time": r[4],
            "latitude": r[5],
            "longitude": r[6],
        }
        for r in rows
    ]


def get_earthquakes(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM earthquakes ORDER BY time DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_flood(f: Dict[str, Any]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO floods
            (id, location, place, severity, time, latitude, longitude, details, risk,
             rainfall_24h_mm, soil_moisture, slope_deg, ndvi, plant_density)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f["id"],
                f.get("location") or f.get("place"),
                f.get("place") or f.get("location"),
                f.get("severity"),
                f.get("time"),
                f.get("latitude"),
                f.get("longitude"),
                f.get("details"),
                f.get("risk"),
                f.get("rainfall_24h_mm"),
                f.get("soil_moisture"),
                f.get("slope_deg"),
                f.get("ndvi"),
                f.get("plant_density"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_floods():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, COALESCE(location, place) AS location, severity, time, latitude, longitude, details
        FROM floods
        ORDER BY time DESC
        LIMIT 50
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "location": r[1],
            "severity": r[2],
            "time": r[3],
            "latitude": r[4],
            "longitude": r[5],
            "details": r[6],
        }
        for r in rows
    ]


def get_floods(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM floods ORDER BY time DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_landslide(l: Dict[str, Any]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO landslides
            (id, location, place, severity, time, latitude, longitude, details, risk,
             rainfall_24h_mm, soil_moisture, slope_deg, ndvi, plant_density)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                l["id"],
                l.get("location") or l.get("place"),
                l.get("place") or l.get("location"),
                l.get("severity"),
                l.get("time"),
                l.get("latitude"),
                l.get("longitude"),
                l.get("details"),
                l.get("risk"),
                l.get("rainfall_24h_mm"),
                l.get("soil_moisture"),
                l.get("slope_deg"),
                l.get("ndvi"),
                l.get("plant_density"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_landslides():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, COALESCE(location, place) AS location, severity, time, latitude, longitude, details
        FROM landslides
        ORDER BY time DESC
        LIMIT 50
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "location": r[1],
            "severity": r[2],
            "time": r[3],
            "latitude": r[4],
            "longitude": r[5],
            "details": r[6],
        }
        for r in rows
    ]


def get_landslides(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM landslides ORDER BY time DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    timestamp = alert.get("timestamp")
    if timestamp is None and alert.get("created_at"):
        try:
            from datetime import datetime

            timestamp = datetime.utcfromtimestamp(int(alert["created_at"]) / 1000).isoformat() + "Z"
        except Exception:
            timestamp = None

    location = alert.get("location")
    if not location:
        region = alert.get("region")
        lat = alert.get("lat")
        lon = alert.get("lon")
        location = region or (f"{lat:.3f}, {lon:.3f}" if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) else "Unknown")

    record = {
        "type": alert.get("type"),
        "level": alert.get("level"),
        "message": alert.get("message"),
        "lat": alert.get("lat"),
        "lon": alert.get("lon"),
        "created_at": alert.get("created_at"),
        "alert_type": alert.get("alert_type"),
        "disaster": alert.get("disaster"),
        "region": alert.get("region"),
        "confidence": alert.get("confidence"),
        "risk_score": alert.get("risk_score"),
        "timestamp": timestamp,
        "location": location,
        "priority": alert.get("priority") or alert.get("level"),
    }
    cur.execute(
        """
        INSERT INTO alerts(type, level, message, lat, lon, created_at, alert_type, disaster, region,
                           confidence, risk_score, timestamp, location, priority)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            record["type"],
            record["level"],
            record["message"],
            record["lat"],
            record["lon"],
            record["created_at"],
            record["alert_type"],
            record["disaster"],
            record["region"],
            record["confidence"],
            record["risk_score"],
            record["timestamp"],
            record["location"],
            record["priority"],
        ),
    )
    record["id"] = cur.lastrowid
    conn.commit()
    conn.close()
    return record


def get_alerts(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY created_at DESC, id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sync_state(key, default=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM sync_state WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_sync_state(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sync_state(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def increment_sync_counter(key: str, amount: int = 1) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM sync_state WHERE key=?", (key,))
    row = cur.fetchone()
    current = 0
    if row:
        try:
            current = int(row["value"])
        except (TypeError, ValueError):
            current = 0
    current += int(amount)
    cur.execute(
        """
        INSERT INTO sync_state(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, str(current)),
    )
    conn.commit()
    conn.close()
    return current

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "disasters.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(cur, table_name, column_name, ddl):
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = {row[1] for row in cur.fetchall()}
    if column_name not in cols:
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


# -------------------------------
# INIT + MIGRATIONS
# -------------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS earthquakes (
            id TEXT PRIMARY KEY,
            place TEXT,
            magnitude REAL,
            depth REAL,
            time INTEGER,
            latitude REAL,
            longitude REAL,
            last_updated INTEGER
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS floods (
            id TEXT PRIMARY KEY,
            place TEXT,
            risk TEXT,
            time INTEGER,
            latitude REAL,
            longitude REAL,
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
            place TEXT,
            risk TEXT,
            time INTEGER,
            latitude REAL,
            longitude REAL,
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
            confidence REAL
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

    # Safe migrations for existing DBs
    _ensure_column(cur, "earthquakes", "last_updated", "last_updated INTEGER")
    for table in ("floods", "landslides"):
        _ensure_column(cur, table, "risk", "risk TEXT")
        _ensure_column(cur, table, "rainfall_24h_mm", "rainfall_24h_mm REAL")
        _ensure_column(cur, table, "soil_moisture", "soil_moisture REAL")
        _ensure_column(cur, table, "slope_deg", "slope_deg REAL")
        _ensure_column(cur, table, "ndvi", "ndvi REAL")
        _ensure_column(cur, table, "plant_density", "plant_density REAL")

    _ensure_column(cur, "alerts", "alert_type", "alert_type TEXT")
    _ensure_column(cur, "alerts", "disaster", "disaster TEXT")
    _ensure_column(cur, "alerts", "region", "region TEXT")
    _ensure_column(cur, "alerts", "confidence", "confidence REAL")

    conn.commit()
    conn.close()


# -------------------------------
# Sync state
# -------------------------------
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


# -------------------------------
# Earthquakes
# -------------------------------
def insert_earthquake(q):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO earthquakes(id, place, magnitude, depth, time, latitude, longitude, last_updated)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            place=excluded.place,
            magnitude=excluded.magnitude,
            depth=excluded.depth,
            time=excluded.time,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            last_updated=excluded.last_updated
        """,
        (
            q["id"],
            q["place"],
            q["magnitude"],
            q["depth"],
            q["time"],
            q["latitude"],
            q["longitude"],
            q.get("last_updated"),
        ),
    )
    conn.commit()
    conn.close()


def get_earthquakes(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM earthquakes ORDER BY time DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -------------------------------
# Floods
# -------------------------------
def insert_flood(f):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO floods(id, place, risk, time, latitude, longitude, rainfall_24h_mm, soil_moisture, slope_deg, ndvi, plant_density)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            place=excluded.place,
            risk=excluded.risk,
            time=excluded.time,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            rainfall_24h_mm=excluded.rainfall_24h_mm,
            soil_moisture=excluded.soil_moisture,
            slope_deg=excluded.slope_deg,
            ndvi=excluded.ndvi,
            plant_density=excluded.plant_density
        """,
        (
            f["id"],
            f["place"],
            f["risk"],
            f["time"],
            f["latitude"],
            f["longitude"],
            f.get("rainfall_24h_mm"),
            f.get("soil_moisture"),
            f.get("slope_deg"),
            f.get("ndvi"),
            f.get("plant_density"),
        ),
    )
    conn.commit()
    conn.close()


def get_floods(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM floods ORDER BY time DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -------------------------------
# Landslides
# -------------------------------
def insert_landslide(l):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO landslides(id, place, risk, time, latitude, longitude, rainfall_24h_mm, soil_moisture, slope_deg, ndvi, plant_density)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            place=excluded.place,
            risk=excluded.risk,
            time=excluded.time,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            rainfall_24h_mm=excluded.rainfall_24h_mm,
            soil_moisture=excluded.soil_moisture,
            slope_deg=excluded.slope_deg,
            ndvi=excluded.ndvi,
            plant_density=excluded.plant_density
        """,
        (
            l["id"],
            l["place"],
            l["risk"],
            l["time"],
            l["latitude"],
            l["longitude"],
            l.get("rainfall_24h_mm"),
            l.get("soil_moisture"),
            l.get("slope_deg"),
            l.get("ndvi"),
            l.get("plant_density"),
        ),
    )
    conn.commit()
    conn.close()


def get_landslides(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM landslides ORDER BY time DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -------------------------------
# Alerts
# -------------------------------
def insert_alert(a):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO alerts(type, level, message, lat, lon, created_at, alert_type, disaster, region, confidence)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            a.get("type") or a.get("alert_type"),
            a["level"],
            a["message"],
            a.get("lat"),
            a.get("lon"),
            a["created_at"],
            a.get("alert_type") or a.get("type"),
            a.get("disaster"),
            a.get("region") or a.get("place"),
            a.get("confidence"),
        ),
    )
    conn.commit()
    conn.close()


def get_alerts(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

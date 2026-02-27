import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "disasters.db")

print("DB PATH:", DB_PATH)
print("DB EXISTS:", os.path.exists(DB_PATH))

try:
    _conn = sqlite3.connect(DB_PATH)
    _cursor = _conn.cursor()
    _cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    _tables = _cursor.fetchall()
    print("TABLES FOUND:", _tables)
    _conn.close()
except Exception as e:
    print("DB CONNECTION ERROR:", e)

def get_connection():
    return sqlite3.connect(DB_PATH)


# Compatibility layer for existing modules that import get_conn/get_* APIs.
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ---------------- EARTHQUAKES ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS earthquakes (
            id TEXT PRIMARY KEY,
            place TEXT,
            magnitude REAL,
            time INTEGER,
            latitude REAL,
            longitude REAL,
            depth REAL
        )
    """)

    # ---------------- FLOODS ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS floods (
            id TEXT PRIMARY KEY,
            location TEXT,
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
    """)

    # ---------------- LANDSLIDES ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS landslides (
            id TEXT PRIMARY KEY,
            location TEXT,
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
    """)

    # ---------------- ALERTS ----------------
    cur.execute("""
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
    """)

    # ---------------- SYNC STATE ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


# ======================= EARTHQUAKES =======================

def insert_earthquake(q):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT OR IGNORE INTO earthquakes
            (id, place, magnitude, time, latitude, longitude, depth)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            q["id"],
            q["place"],
            q["magnitude"],
            q["time"],
            q["latitude"],
            q["longitude"],
            q["depth"],
        ))
        conn.commit()
    except Exception as e:
        print("❌ insert_earthquake error:", e)
    finally:
        conn.close()


def get_all_earthquakes():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, place, magnitude, depth, time, latitude, longitude
        FROM earthquakes
        ORDER BY time DESC
        LIMIT 50
    """)

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


# ======================= FLOODS =======================

def insert_flood(f):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT OR IGNORE INTO floods
            (id, location, severity, time, latitude, longitude, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f["id"],
            f["location"],
            f["severity"],
            f["time"],
            f["latitude"],
            f["longitude"],
            f["details"],
        ))
        conn.commit()
    except Exception as e:
        print("❌ insert_flood error:", e)
    finally:
        conn.close()


def get_all_floods():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, location, severity, time, latitude, longitude, details
        FROM floods
        ORDER BY time DESC
        LIMIT 50
    """)

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


# ======================= LANDSLIDES =======================

def insert_landslide(l):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT OR IGNORE INTO landslides
            (id, location, severity, time, latitude, longitude, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            l["id"],
            l["location"],
            l["severity"],
            l["time"],
            l["latitude"],
            l["longitude"],
            l["details"],
        ))
        conn.commit()
    except Exception as e:
        print("❌ insert_landslide error:", e)
    finally:
        conn.close()


def get_all_landslides():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, location, severity, time, latitude, longitude, details
        FROM landslides
        ORDER BY time DESC
        LIMIT 50
    """)

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


def insert_alert(alert):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO alerts(type, level, message, lat, lon, created_at, alert_type, disaster, region, confidence)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            alert.get("type"),
            alert.get("level"),
            alert.get("message"),
            alert.get("lat"),
            alert.get("lon"),
            alert.get("created_at"),
            alert.get("alert_type"),
            alert.get("disaster"),
            alert.get("region"),
            alert.get("confidence"),
        ),
    )
    conn.commit()
    conn.close()


def get_alerts(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))
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

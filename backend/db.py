import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "disasters.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# INIT
# -------------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Earthquakes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS earthquakes (
        id TEXT PRIMARY KEY,
        place TEXT,
        magnitude REAL,
        depth REAL,
        time INTEGER,
        latitude REAL,
        longitude REAL
    )
    """)

    # Floods (simple demo data)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS floods (
        id TEXT PRIMARY KEY,
        place TEXT,
        risk TEXT,
        time INTEGER,
        latitude REAL,
        longitude REAL
    )
    """)

    # Landslides (simple demo data)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS landslides (
        id TEXT PRIMARY KEY,
        place TEXT,
        risk TEXT,
        time INTEGER,
        latitude REAL,
        longitude REAL
    )
    """)

    # Alerts (auto-generated)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        level TEXT,
        message TEXT,
        lat REAL,
        lon REAL,
        created_at INTEGER
    )
    """)

    conn.commit()
    conn.close()


# -------------------------------
# Earthquakes
# -------------------------------
def insert_earthquake(q):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR IGNORE INTO earthquakes(id, place, magnitude, depth, time, latitude, longitude)
    VALUES(?,?,?,?,?,?,?)
    """, (
        q["id"], q["place"], q["magnitude"], q["depth"], q["time"], q["latitude"], q["longitude"]
    ))
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
    cur.execute("""
    INSERT OR IGNORE INTO floods(id, place, risk, time, latitude, longitude)
    VALUES(?,?,?,?,?,?)
    """, (
        f["id"], f["place"], f["risk"], f["time"], f["latitude"], f["longitude"]
    ))
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
    cur.execute("""
    INSERT OR IGNORE INTO landslides(id, place, risk, time, latitude, longitude)
    VALUES(?,?,?,?,?,?)
    """, (
        l["id"], l["place"], l["risk"], l["time"], l["latitude"], l["longitude"]
    ))
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
    cur.execute("""
    INSERT INTO alerts(type, level, message, lat, lon, created_at)
    VALUES(?,?,?,?,?,?)
    """, (
        a["type"], a["level"], a["message"], a.get("lat"), a.get("lon"), a["created_at"]
    ))
    conn.commit()
    conn.close()

def get_alerts(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "disasters.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ✅ Earthquakes table
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

    # ✅ Floods table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS floods (
        id TEXT PRIMARY KEY,
        location TEXT,
        severity TEXT,
        time INTEGER,
        latitude REAL,
        longitude REAL,
        details TEXT
    )
    """)

    # ✅ Landslides table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS landslides (
        id TEXT PRIMARY KEY,
        location TEXT,
        severity TEXT,
        time INTEGER,
        latitude REAL,
        longitude REAL,
        details TEXT
    )
    """)

    conn.commit()
    conn.close()


# ------------------ EARTHQUAKES ------------------

def insert_earthquake(quake):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO earthquakes (id, place, magnitude, time, latitude, longitude, depth)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        quake["id"],
        quake["place"],
        quake["magnitude"],
        quake["time"],
        quake["latitude"],
        quake["longitude"],
        quake["depth"]
    ))

    conn.commit()
    conn.close()


def get_all_earthquakes():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, place, magnitude, time, latitude, longitude, depth FROM earthquakes ORDER BY time DESC")
    rows = cur.fetchall()

    conn.close()

    return [
        {
            "id": r[0],
            "place": r[1],
            "magnitude": r[2],
            "time": r[3],
            "latitude": r[4],
            "longitude": r[5],
            "depth": r[6],
        }
        for r in rows
    ]


# ------------------ FLOODS ------------------

def insert_flood(flood):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO floods (id, location, severity, time, latitude, longitude, details)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        flood["id"],
        flood["location"],
        flood["severity"],
        flood["time"],
        flood["latitude"],
        flood["longitude"],
        flood["details"]
    ))

    conn.commit()
    conn.close()


def get_all_floods():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, location, severity, time, latitude, longitude, details FROM floods ORDER BY time DESC")
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


# ------------------ LANDSLIDES ------------------

def insert_landslide(landslide):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO landslides (id, location, severity, time, latitude, longitude, details)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        landslide["id"],
        landslide["location"],
        landslide["severity"],
        landslide["time"],
        landslide["latitude"],
        landslide["longitude"],
        landslide["details"]
    ))

    conn.commit()
    conn.close()


def get_all_landslides():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, location, severity, time, latitude, longitude, details FROM landslides ORDER BY time DESC")
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

import sqlite3
import json
from datetime import datetime

DB_PATH = "database/properties.db"

def init_nhis_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS nhis_informal_settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            local_authority TEXT,
            settlement_name TEXT,
            is_profiled TEXT,
            is_planned TEXT,
            is_surveyed TEXT,
            land_ownership TEXT,
            tenure_security TEXT,
            number_of_erven INTEGER,
            congestion_status TEXT,
            communal_facilities TEXT,
            bulk_services TEXT,
            upgrade_level INTEGER,
            date_loaded TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("NHIS informal settlements table created.")

ERONGO_SETTLEMENTS = [
    ("Erongo", "Arandis", "Rossing Heights Proper", "No", "Yes", "Yes", "Local Authority", "Leasehold", 284, "Decongested", "None", "Not Applicable", 1),
    ("Erongo", "Hentiesbay", "!Goas", "Yes", "Yes", "Yes", "Local Authority", "Leasehold", 172, "Congested", "Communal tap", "Water, Sewer, Electricity", 4),
    ("Erongo", "Karibib", "Harambe Extension 7", "Yes", "Yes", "Yes", "Local Authority", "Freehold", 347, "Decongested", "None", "Water, Sewer, Electricity", 4),
    ("Erongo", "Karibib", "Harambe Extension 8", "Unknown", "Yes", "Yes", "Local Authority", "Freehold", 339, "Decongested", "Communal tap", "Water", 2),
    ("Erongo", "Karibib", "Harambe Extension 9", "Unknown", "Yes", "Yes", "Local Authority", "Freehold", 339, "Congested", "Communal tap", "Water", 2),
    ("Erongo", "Karibib", "New Location", "Unknown", "Yes", "Yes", "Local Authority", "Freehold", 165, "Decongested", "None", "Not Applicable", 1),
    ("Erongo", "Karibib", "Old Location", "Unknown", "Yes", "Yes", "Local Authority", "Freehold", 324, "Decongested", "None", "Not Applicable", 1),
    ("Erongo", "Karibib", "Usab Informal Settlement", "Yes", "Yes", "Yes", "Local Authority", "Freehold", 717, "Decongested", "None", "Water, Sewer, Electricity", 4),
    ("Erongo", "Omaruru", "7de Laan Extension 8", "Yes", "Yes", "Yes", "Local Authority", "Freehold", 643, "Decongested", "Communal tap", "Electricity", 2),
    ("Erongo", "Omaruru", "7de Laan Extension 9", "Yes", "Yes", "Yes", "Local Authority", "Freehold", 643, "Decongested", "Communal tap", "Electricity", 2),
    ("Erongo", "Swakopmund", "3 Housing Groups A", "Yes", "Yes", "Yes", "Local Authority", "Certificate of Occupancy", 283, "Decongested", "None", "Not Applicable", 1),
    ("Erongo", "Swakopmund", "3 Housing Groups B", "Yes", "Yes", "Yes", "Local Authority", "Certificate of Occupancy", 313, "Decongested", "None", "Not Applicable", 1),
    ("Erongo", "Swakopmund", "DRC Airport", "Yes", "Yes", "Yes", "Local Authority", "Certificate of Occupancy", 314, "Congested", "Communal tap", "Not Applicable", 1),
    ("Erongo", "Usakos", "Onguluumbashe", "Yes", "Yes", "Yes", "Local Authority", "Leasehold", 442, "Congested", "Communal tap", "Water, Electricity", 3),
    ("Erongo", "Usakos", "Erongosig Extension 2", "No", "No", "Yes", "Local Authority", "Leasehold", 9999, "Decongested", "Communal tap", "Water, Sewer", 3),
    ("Erongo", "Usakos", "Erongosig Extension 3", "No", "No", "Yes", "Local Authority", "Leasehold", 9999, "Decongested", "Communal tap", "Water, Sewer", 3),
    ("Erongo", "Usakos", "Saamstaan", "Yes", "Yes", "Yes", "Local Authority", "Leasehold", 220, "Congested", "Communal tap", "Water, Sewer", 3),
]

def load_erongo_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    date_loaded = datetime.now().strftime("%Y-%m-%d")
    for s in ERONGO_SETTLEMENTS:
        c.execute("""
            INSERT INTO nhis_informal_settlements 
            (region, local_authority, settlement_name, is_profiled, is_planned,
             is_surveyed, land_ownership, tenure_security, number_of_erven,
             congestion_status, communal_facilities, bulk_services, upgrade_level, date_loaded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (*s, date_loaded))
    conn.commit()
    conn.close()
    print(f"Loaded {len(ERONGO_SETTLEMENTS)} Erongo informal settlements into database.")

def print_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT local_authority, COUNT(*), AVG(upgrade_level) FROM nhis_informal_settlements GROUP BY local_authority")
    rows = c.fetchall()
    print("\n--- NHIS ERONGO SUMMARY ---")
    for r in rows:
        print(f"{r[0]}: {r[1]} settlements, avg upgrade level {round(r[2],1)}")
    
    c.execute("SELECT settlement_name, congestion_status, bulk_services, upgrade_level FROM nhis_informal_settlements WHERE local_authority='Swakopmund'")
    rows = c.fetchall()
    print("\nSwakopmund settlements:")
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2]} | Level {r[3]}")
    conn.close()

if __name__ == "__main__":
    init_nhis_table()
    load_erongo_data()
    print_summary()

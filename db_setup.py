import sqlite3
import sqlite3



def create_database():
    conn = sqlite3.connect("../database/entity_resolution.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_records (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        source TEXT,
        last_updated TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidate_matches (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id_1 INTEGER,
        record_id_2 INTEGER,
        confidence_score REAL,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS golden_records (
        golden_id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_name TEXT,
        canonical_email TEXT,
        canonical_phone TEXT,
        canonical_address TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lineage (
        lineage_id INTEGER PRIMARY KEY AUTOINCREMENT,
        golden_id INTEGER,
        source_record_id INTEGER,
        merged_at TEXT
    )
    """)

    cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id_1 INTEGER,
    record_id_2 INTEGER,
    decision TEXT,
    reviewed_at TEXT
)
""")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Database created successfully")
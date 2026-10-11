import sqlite3
from datetime import datetime

from src.golden_record import create_golden_records


def save_feedback(record1, record2, decision):
    conn = sqlite3.connect("database/entity_resolution.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id_1 INTEGER,
        record_id_2 INTEGER,
        decision TEXT,
        reviewed_at TEXT
    )
    """)

    cursor.execute("""
    INSERT INTO feedback
    (record_id_1, record_id_2, decision, reviewed_at)
    VALUES (?, ?, ?, ?)
    """, (
        record1,
        record2,
        decision,
        str(datetime.now())
    ))

    # update decision table
    new_decision = (
        "AUTO_MERGE"
        if decision == "APPROVED"
        else "REJECTED"
    )

    cursor.execute("""
    UPDATE match_decisions
    SET decision = ?
    WHERE record_id_1 = ? AND record_id_2 = ?
    """, (
        new_decision,
        record1,
        record2
    ))

    conn.commit()
    conn.close()

    # refresh golden records automatically
    create_golden_records()
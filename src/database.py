"""
Database Module
Persists processed candidate profiles to a local SQLite database.
Table: candidates
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "candidates.db")


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the candidates table if it doesn't already exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id       TEXT,
                resume_name        TEXT,
                full_name          TEXT,
                email              TEXT,
                phone              TEXT,
                location           TEXT,
                years_experience   REAL,
                skills_count       INTEGER,
                overall_confidence REAL,
                sources_count      INTEGER,
                final_profile      TEXT,
                projected_profile  TEXT,
                processed_at       TEXT
            )
        """)
        conn.commit()


def save_candidate(resume_name, final_profile, projected_profile, sources_count):
    """
    Insert a fully processed candidate into the database.
    Returns the new row id.
    """
    emails = final_profile.get("emails") or []
    phones = final_profile.get("phones") or []
    loc = final_profile.get("location")
    location_str = (
        f"{loc.get('city', '')}, {loc.get('country', '')}".strip(", ")
        if loc else ""
    )

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO candidates
                (candidate_id, resume_name, full_name, email, phone,
                 location, years_experience, skills_count, overall_confidence,
                 sources_count, final_profile, projected_profile, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                final_profile.get("candidate_id", ""),
                resume_name,
                final_profile.get("full_name", ""),
                emails[0] if emails else "",
                phones[0] if phones else "",
                location_str,
                final_profile.get("years_experience") or 0.0,
                len(final_profile.get("skills") or []),
                final_profile.get("overall_confidence", 0.0),
                sources_count,
                json.dumps(final_profile),
                json.dumps(projected_profile),
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_all_candidates(limit=200):
    """Return all candidates ordered by most recent first."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, candidate_id, resume_name, full_name, email, phone,
                   location, years_experience, skills_count, overall_confidence,
                   sources_count, processed_at
            FROM candidates
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_candidate_by_id(row_id):
    """Return one full candidate record (including JSON blobs) by its row id."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM candidates WHERE id = ?", (row_id,)
        ).fetchone()
    if row:
        result = dict(row)
        result["final_profile"] = json.loads(result["final_profile"])
        result["projected_profile"] = json.loads(result["projected_profile"])
        return result
    return None


def delete_candidate(row_id):
    """Delete a single candidate by row id."""
    with _connect() as conn:
        conn.execute("DELETE FROM candidates WHERE id = ?", (row_id,))
        conn.commit()


def clear_all_candidates():
    """Wipe the entire candidates table."""
    with _connect() as conn:
        conn.execute("DELETE FROM candidates")
        conn.commit()


def get_stats():
    """Return aggregate statistics for the dashboard."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                          AS total,
                ROUND(AVG(overall_confidence), 2) AS avg_confidence,
                ROUND(AVG(skills_count), 1)       AS avg_skills,
                ROUND(AVG(years_experience), 1)   AS avg_experience
            FROM candidates
            """
        ).fetchone()
    return dict(row) if row else {}

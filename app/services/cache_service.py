import sqlite3
import json
from datetime import datetime

DB_NAME = "database/cache.db"


def initialize_database():
    """
    Creates the SQLite database and summaries table
    if it does not already exist.
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries(

            video_id TEXT PRIMARY KEY,

            summary TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
        """)

        conn.commit()


def get_summary(video_id: str):
    """
    Returns a cached summary if it exists.
    Otherwise returns None.
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT summary
            FROM summaries
            WHERE video_id = ?
            """,
            (video_id,)
        )

        result = cursor.fetchone()

        if result:
            #converts the JSON string back into a Python dictionary
            return json.loads(result[0])

        return None
    
def save_summary(video_id: str, summary: dict):
    """
    Save a summary in the database.
    If the video already exists, update the summary.
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO summaries
            (video_id, summary, created_at)
            VALUES (?, ?, ?)
            """,
            (
                video_id,
                json.dumps(summary),
                datetime.now().isoformat()
            )
        )

        conn.commit()
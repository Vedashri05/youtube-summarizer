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
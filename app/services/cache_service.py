import json
import sqlite3
from datetime import datetime

import numpy as np

DB_NAME = "database/cache.db"


def initialize_database():
    """
    Creates the SQLite database and the tables we need if they do not
    already exist, and migrates the summaries table if it was created by
    an older version of this app (before summary modes existed).
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries(

            video_id TEXT NOT NULL,

            -- One video can now have up to 4 cached summaries (one per
            -- mode), so the primary key is the PAIR, not video_id alone.
            mode TEXT NOT NULL DEFAULT 'technical',

            summary TEXT NOT NULL,

            created_at TEXT NOT NULL,

            PRIMARY KEY (video_id, mode)

        )
        """)

        _migrate_summaries_table_if_needed(cursor)

        # ------------------------------------------------------------------
        # Vector index table.
        #
        # One row = one transcript chunk + its embedding.
        # The embedding is stored as a raw float32 BLOB (np.tobytes) rather
        # than JSON: it is ~4x smaller and loads back with zero parsing.
        # Chunks/embeddings do NOT depend on summary mode - a video is
        # indexed once regardless of which summary style is requested.
        # ------------------------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            video_id TEXT NOT NULL,

            chunk_index INTEGER NOT NULL,

            start_time REAL NOT NULL,

            end_time REAL NOT NULL,

            text TEXT NOT NULL,

            embedding BLOB NOT NULL

        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_video_id
        ON chunks(video_id)
        """)

        # ------------------------------------------------------------------
        # Users
        # ------------------------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # ------------------------------------------------------------------
        # Videos - one row per summarization job. This is the state machine
        # backing the async pipeline (status column) AND the "My Videos"
        # history list (everything else). No separate `transcript` column
        # on purpose - raw transcript text already lives in `chunks`, keyed
        # by video_id, so storing it here too would be a second source of
        # truth to keep in sync.
        # ------------------------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            video_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error TEXT,
            summary_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_videos_user_id
        ON videos(user_id)
        """)

        conn.commit()


def _migrate_summaries_table_if_needed(cursor: sqlite3.Cursor):
    """
    If `summaries` already exists from before summary modes were added, it
    has PRIMARY KEY (video_id) and no `mode` column. SQLite cannot change a
    primary key with ALTER TABLE, so we rebuild the table: copy any old
    rows in as mode='technical' (matching this app's previous, only
    behaviour), then swap the new table into place.

    Safe to call every startup - it only acts when the OLD shape is found.
    """

    cursor.execute("PRAGMA table_info(summaries)")
    columns = {row[1] for row in cursor.fetchall()}

    if "mode" in columns:
        return  # already the new shape, nothing to do

    cursor.execute("ALTER TABLE summaries RENAME TO summaries_old")

    cursor.execute("""
    CREATE TABLE summaries(
        video_id TEXT NOT NULL,
        mode TEXT NOT NULL DEFAULT 'technical',
        summary TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (video_id, mode)
    )
    """)

    cursor.execute("""
    INSERT INTO summaries (video_id, mode, summary, created_at)
    SELECT video_id, 'technical', summary, created_at FROM summaries_old
    """)

    cursor.execute("DROP TABLE summaries_old")


# ---------------------------------------------------------------------------
# Summary cache - keyed by (video_id, mode)
# ---------------------------------------------------------------------------
def get_summary(video_id: str, mode: str):
    """
    Returns a cached summary for this video IN THIS MODE, if it exists.
    A cached "beginner" summary is never returned for a "technical" request
    - each mode is generated and cached independently.
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT summary
            FROM summaries
            WHERE video_id = ? AND mode = ?
            """,
            (video_id, mode)
        )

        result = cursor.fetchone()

        if result:
            return json.loads(result[0])

        return None


def save_summary(video_id: str, mode: str, summary: dict):
    """
    Save a summary for this (video, mode) pair. Re-summarizing the same
    video in the same mode overwrites; a different mode is a separate row.
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO summaries
            (video_id, mode, summary, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                video_id,
                mode,
                json.dumps(summary),
                datetime.now().isoformat()
            )
        )

        conn.commit()


# ---------------------------------------------------------------------------
# Chunk / embedding store (unchanged - shared across all summary modes)
# ---------------------------------------------------------------------------
def is_video_indexed(video_id: str) -> bool:
    """
    True if we have already chunked and embedded this video.
    Embeddings cost an API call, so we never redo this work.
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM chunks WHERE video_id = ? LIMIT 1",
            (video_id,)
        )

        return cursor.fetchone() is not None


def save_chunks(video_id: str, chunks: list[dict], embeddings: np.ndarray):
    """
    Store chunks and their vectors.

    Parameters:
        chunks: [{"start": float, "end": float, "text": str}, ...]
        embeddings: numpy array, one row per chunk, same order
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        # Clear any half-written index for this video first
        cursor.execute("DELETE FROM chunks WHERE video_id = ?", (video_id,))

        rows = [
            (
                video_id,
                index,
                chunk["start"],
                chunk["end"],
                chunk["text"],
                embeddings[index].astype(np.float32).tobytes(),
            )
            for index, chunk in enumerate(chunks)
        ]

        cursor.executemany(
            """
            INSERT INTO chunks
            (video_id, chunk_index, start_time, end_time, text, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows
        )

        conn.commit()


def get_chunks(video_id: str):
    """
    Load every chunk for a video.

    Returns:
        (chunks, matrix) where
            chunks is a list of dicts with start / end / text
            matrix is a (n_chunks, dim) float32 numpy array in the same order
    """

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT chunk_index, start_time, end_time, text, embedding
            FROM chunks
            WHERE video_id = ?
            ORDER BY chunk_index
            """,
            (video_id,)
        )

        rows = cursor.fetchall()

    if not rows:
        return [], np.empty((0, 0), dtype=np.float32)

    chunks = [
        {
            "chunk_index": row[0],
            "start": row[1],
            "end": row[2],
            "text": row[3],
        }
        for row in rows
    ]

    matrix = np.vstack([
        np.frombuffer(row[4], dtype=np.float32)
        for row in rows
    ])

    return chunks, matrix


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def create_user(email: str, hashed_password: str) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (email, hashed_password, created_at)
            VALUES (?, ?, ?)
            """,
            (email, hashed_password, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid


def get_user_by_email(email: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, hashed_password FROM users WHERE email = ?",
            (email,)
        )
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "email": row[1], "hashed_password": row[2]}
        return None


# ---------------------------------------------------------------------------
# Video jobs - the async pipeline's state machine lives here, plus the
# "My Videos" history list
# ---------------------------------------------------------------------------
def create_video_job(user_id: int, url: str, video_id: str, mode: str) -> int:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO videos
            (user_id, url, video_id, mode, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """,
            (user_id, url, video_id, mode, now, now)
        )
        conn.commit()
        return cursor.lastrowid


def update_video_status(job_id: int, status: str, error: str | None = None):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE videos SET status = ?, error = ?, updated_at = ? WHERE id = ?",
            (status, error, datetime.now().isoformat(), job_id)
        )
        conn.commit()


def save_video_result(job_id: int, summary: dict):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE videos
            SET status = 'complete', summary_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(summary), datetime.now().isoformat(), job_id)
        )
        conn.commit()


def get_video_job(job_id: int, user_id: int):
    """
    Scoped to the owner - one user can never poll or read another user's
    job just by guessing an id.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, url, video_id, mode, status, error, summary_json,
                   created_at, updated_at
            FROM videos
            WHERE id = ? AND user_id = ?
            """,
            (job_id, user_id)
        )
        row = cursor.fetchone()
        return _video_row_to_dict(row) if row else None


def get_video_job_by_video_id(video_id: str, user_id: int):
    """
    Used to check that a user owns a given (already-processed) video
    before letting them /chat or /search against it.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, url, video_id, mode, status, error, summary_json,
                   created_at, updated_at
            FROM videos
            WHERE video_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (video_id, user_id)
        )
        row = cursor.fetchone()
        return _video_row_to_dict(row) if row else None


def list_user_videos(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, url, video_id, mode, status, error, summary_json,
                   created_at, updated_at
            FROM videos
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        return [_video_row_to_dict(row) for row in cursor.fetchall()]


def _video_row_to_dict(row):
    summary = json.loads(row[6]) if row[6] else None

    return {
        "id": row[0],
        "url": row[1],
        "video_id": row[2],
        "mode": row[3],
        "status": row[4],
        "error": row[5],
        "summary": summary,
        "created_at": row[7],
        "updated_at": row[8],
        # Pulled up from inside summary_json so the frontend doesn't have
        # to reach into a nested (and possibly null) object just to show
        # a list item's name.
        "title": summary.get("title") if summary else None,
    }
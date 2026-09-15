"""Small SQLite connection and schema manager."""
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL UNIQUE,
 full_name TEXT NOT NULL, department TEXT, email TEXT, active INTEGER NOT NULL DEFAULT 1,
 face_image_path TEXT NOT NULL, embedding BLOB NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS attendance (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, attendance_date TEXT NOT NULL,
 check_in TEXT NOT NULL, confidence REAL NOT NULL, source TEXT NOT NULL DEFAULT 'camera',
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 UNIQUE(user_id, attendance_date)
);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_users_name ON users(full_name);
"""


def get_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as connection:
        connection.executescript(SCHEMA)

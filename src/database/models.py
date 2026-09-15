import sqlite3
from typing import Iterable
import numpy as np
from src.database.db import get_connection


class Repository:
    def __init__(self, database_path):
        self.database_path = database_path

    def admin_count(self) -> int:
        with get_connection(self.database_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]

    def create_admin(self, username: str, password_hash: str) -> None:
        with get_connection(self.database_path) as conn:
            conn.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", (username, password_hash))

    def get_admin(self, username: str):
        with get_connection(self.database_path) as conn:
            return conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()

    def create_user(self, employee_id, full_name, department, email, image_path, embedding):
        blob = np.asarray(embedding, dtype=np.float32).tobytes()
        with get_connection(self.database_path) as conn:
            cursor = conn.execute("""INSERT INTO users
                (employee_id, full_name, department, email, face_image_path, embedding)
                VALUES (?, ?, ?, ?, ?, ?)""", (employee_id, full_name, department, email, image_path, blob))
            return cursor.lastrowid

    def list_users(self, query=""):
        with get_connection(self.database_path) as conn:
            return conn.execute("""SELECT id, employee_id, full_name, department, email, active, created_at
                FROM users WHERE employee_id LIKE ? OR full_name LIKE ? OR department LIKE ? ORDER BY full_name""",
                tuple([f"%{query}%"] * 3)).fetchall()

    def set_user_active(self, user_id: int, active: bool) -> None:
        with get_connection(self.database_path) as conn:
            conn.execute("UPDATE users SET active = ? WHERE id = ?", (int(active), user_id))

    def embeddings(self) -> Iterable:
        with get_connection(self.database_path) as conn:
            rows = conn.execute("SELECT id, employee_id, full_name, embedding FROM users WHERE active = 1").fetchall()
        return [(dict(row), np.frombuffer(row["embedding"], dtype=np.float32)) for row in rows]

    def attendance_exists(self, user_id, date) -> bool:
        with get_connection(self.database_path) as conn:
            return conn.execute("SELECT 1 FROM attendance WHERE user_id = ? AND attendance_date = ?", (user_id, date)).fetchone() is not None

    def mark_attendance(self, user_id, attendance_date, check_in, confidence):
        try:
            with get_connection(self.database_path) as conn:
                conn.execute("""INSERT INTO attendance (user_id, attendance_date, check_in, confidence)
                    VALUES (?, ?, ?, ?)""", (user_id, attendance_date, check_in, confidence))
            return True
        except sqlite3.IntegrityError:
            return False

    def attendance(self, query="", date=""):
        sql = """SELECT a.id, a.attendance_date, a.check_in, a.confidence, u.employee_id, u.full_name, u.department
               FROM attendance a JOIN users u ON a.user_id = u.id WHERE 1=1"""
        args = []
        if query:
            sql += " AND (u.full_name LIKE ? OR u.employee_id LIKE ? OR u.department LIKE ?)"
            args.extend([f"%{query}%"] * 3)
        if date:
            sql += " AND a.attendance_date = ?"; args.append(date)
        sql += " ORDER BY a.check_in DESC"
        with get_connection(self.database_path) as conn:
            return conn.execute(sql, args).fetchall()

    def dashboard_counts(self):
        with get_connection(self.database_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM users WHERE active = 1").fetchone()[0]
            today = conn.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date = date('now', 'localtime')").fetchone()[0]
            recent = conn.execute("""SELECT a.check_in, u.full_name, u.employee_id FROM attendance a JOIN users u ON u.id=a.user_id
                ORDER BY a.check_in DESC LIMIT 8""").fetchall()
        return total, today, recent

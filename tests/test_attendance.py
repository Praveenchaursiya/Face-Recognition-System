from pathlib import Path
from src.database.db import initialize_database
from src.database.models import Repository


def test_duplicate_attendance_is_prevented(tmp_path: Path):
    database = tmp_path / "test.db"
    initialize_database(database)
    repo = Repository(database)
    user_id = repo.create_user("E001", "Test User", "QA", "", "face.jpg", [0.1, 0.2])
    assert repo.mark_attendance(user_id, "2026-01-01", "2026-01-01T09:00:00", 0.9)
    assert not repo.mark_attendance(user_id, "2026-01-01", "2026-01-01T10:00:00", 0.9)

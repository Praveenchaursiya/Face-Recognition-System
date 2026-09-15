from datetime import datetime


class AttendanceService:
    def __init__(self, repository):
        self.repository = repository

    def record(self, user_id: int, confidence: float):
        now = datetime.now()
        created = self.repository.mark_attendance(user_id, now.date().isoformat(), now.isoformat(timespec="seconds"), confidence)
        return created, now

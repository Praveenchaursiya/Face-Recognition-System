import numpy as np


class FaceRecognizer:
    def __init__(self, repository, encoder, detector, threshold=0.45):
        self.repository = repository
        self.encoder = encoder
        self.detector = detector
        self.threshold = threshold

    @staticmethod
    def cosine_similarity(first: np.ndarray, second: np.ndarray) -> float:
        denominator = np.linalg.norm(first) * np.linalg.norm(second)
        return float(np.dot(first, second) / denominator) if denominator else 0.0

    def recognize(self, image):
        faces = self.detector.detect(image)
        if len(faces) == 0:
            return {"status": "no_face", "message": "No face detected."}
        if len(faces) > 1:
            return {"status": "multiple_faces", "message": "Please present exactly one face."}
        probe = self.encoder.encode(image, faces[0])
        best, score = None, -1.0
        for user, embedding in self.repository.embeddings():
            value = self.cosine_similarity(probe, embedding)
            if value > score:
                best, score = user, value
        if best is None or score < self.threshold:
            return {"status": "unknown", "message": "Unknown face. Attendance was not recorded.", "confidence": round(max(score, 0), 3)}
        return {"status": "recognized", "user": best, "confidence": round(score, 3)}

from pathlib import Path
import cv2


class RegistrationService:
    def __init__(self, detector, encoder, repository, faces_dir: Path):
        self.detector, self.encoder, self.repository = detector, encoder, repository
        self.faces_dir = faces_dir

    def register(self, employee_id, full_name, department, email, image_bytes):
        image = cv2.imdecode(__import__('numpy').frombuffer(image_bytes, __import__('numpy').uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Captured image could not be read.")
        faces = self.detector.detect(image)
        if len(faces) != 1:
            raise ValueError("Registration requires exactly one clearly visible face.")
        embedding = self.encoder.encode(image, faces[0])
        self.faces_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{employee_id}.jpg"
        image_path = self.faces_dir / filename
        if not cv2.imwrite(str(image_path), image):
            raise OSError("Could not securely save the face image.")
        try:
            return self.repository.create_user(employee_id, full_name, department, email, str(image_path), embedding)
        except Exception:
            image_path.unlink(missing_ok=True)
            raise

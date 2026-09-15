"""YuNet face detection backed by OpenCV's maintained DNN API."""
from pathlib import Path
import cv2
import numpy as np


class FaceDetector:
    def __init__(self, model_path: Path):
        if not model_path.exists():
            raise FileNotFoundError(f"Face detector model not found: {model_path}")
        self.model_path = str(model_path)

    def detect(self, image: np.ndarray):
        if image is None or image.size == 0:
            raise ValueError("No image data supplied for face detection.")
        height, width = image.shape[:2]
        detector = cv2.FaceDetectorYN.create(self.model_path, "", (width, height), 0.85, 0.3, 5000)
        _, faces = detector.detect(image)
        return [] if faces is None else faces

    @staticmethod
    def crop(image: np.ndarray, face: np.ndarray) -> np.ndarray:
        x, y, width, height = face[:4].astype(int)
        margin = int(max(width, height) * 0.2)
        x1, y1 = max(0, x - margin), max(0, y - margin)
        x2, y2 = min(image.shape[1], x + width + margin), min(image.shape[0], y + height + margin)
        return image[y1:y2, x1:x2]

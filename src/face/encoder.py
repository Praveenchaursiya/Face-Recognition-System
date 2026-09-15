"""SFace embedding generation and official model bootstrap."""
from pathlib import Path
from urllib.request import urlretrieve
import cv2
import numpy as np

MODELS = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
}


def ensure_models(model_dir: Path) -> dict:
    model_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for filename, url in MODELS.items():
        path = model_dir / filename
        if not path.exists():
            try:
                urlretrieve(url, path)
            except Exception as exc:
                path.unlink(missing_ok=True)
                raise RuntimeError(f"Could not download {filename}. Check internet access or place it in {model_dir}.") from exc
        paths[filename] = path
    return paths


class FaceEncoder:
    def __init__(self, model_path: Path):
        if not model_path.exists():
            raise FileNotFoundError(f"Face recognition model not found: {model_path}")
        self.recognizer = cv2.FaceRecognizerSF.create(str(model_path), "")

    def encode(self, image: np.ndarray, face: np.ndarray) -> np.ndarray:
        aligned = self.recognizer.alignCrop(image, face)
        embedding = self.recognizer.feature(aligned)
        return np.asarray(embedding, dtype=np.float32).flatten()

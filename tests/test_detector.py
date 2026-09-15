import numpy as np
from src.face.detector import FaceDetector


def test_crop_keeps_face_region_inside_image():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    face = np.array([10, 10, 30, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
    cropped = FaceDetector.crop(image, face)
    assert cropped.shape[0] > 30
    assert cropped.shape[1] > 30

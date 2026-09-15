import numpy as np
import pytest
from src.face.recognizer import FaceRecognizer


def test_cosine_similarity_identical_vectors_is_one():
    vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert FaceRecognizer.cosine_similarity(vector, vector) == pytest.approx(1.0)


def test_cosine_similarity_zero_vector_is_safe():
    assert FaceRecognizer.cosine_similarity(np.zeros(2), np.ones(2)) == 0.0

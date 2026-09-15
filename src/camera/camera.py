import threading
import cv2


class Camera:
    """Thread-safe shared webcam stream, opened only while requested."""
    def __init__(self, index=0):
        self.index, self.capture, self.lock = index, None, threading.Lock()

    def _open(self):
        if self.capture is None or not self.capture.isOpened():
            # Different Windows camera drivers expose different OpenCV backends.
            # Try the default backend first, then the two native Windows options.
            backends = (cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF)
            for backend in backends:
                capture = cv2.VideoCapture(self.index, backend)
                if capture.isOpened():
                    self.capture = capture
                    return
                capture.release()
            self.capture = None
            raise RuntimeError(
                "Camera unavailable. Close other apps using the camera, allow camera access "
                "for desktop apps in Windows Privacy settings, then check CAMERA_INDEX."
            )

    def frames(self):
        try:
            self._open()
            while True:
                with self.lock:
                    ok, frame = self.capture.read()
                if not ok:
                    break
                ok, buffer = cv2.imencode(".jpg", frame)
                if ok:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        finally:
            self.release()

    def release(self):
        with self.lock:
            if self.capture is not None:
                self.capture.release(); self.capture = None

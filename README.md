# Face Recognition & Attendance Management System

Local Flask software for webcam employee enrollment, real OpenCV face recognition, and automatic daily attendance. It uses OpenCV Zoo's YuNet detector and SFace embedding model. Camera images and biometric embeddings stay on the local machine; they are never sent to a cloud service.

## Features

- Hashed administrator passwords and protected administration pages
- Secure first-run administrator setup (or environment-driven initial account)
- Webcam enrollment with exactly-one-face validation
- YuNet detection plus SFace embeddings and cosine-similarity matching
- Explicit unknown, no-face, and multiple-face outcomes—never dummy recognition
- SQLite-backed attendance with database-level daily duplicate prevention
- Dashboard, employee activation/deactivation, history search, date filter, and CSV export
- Error pages, file logging, `.env` configuration, and pytest tests

## Install and run on Windows (PowerShell)

```powershell
cd C:\Users\prave_g23e0f2\OneDrive\Desktop\Face_Recognition_System
py -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
notepad .env
pip install -r requirements.txt
python app.py
```

Edit `.env` before running: set a long random `SECRET_KEY`, then either set `ADMIN_USERNAME` and `ADMIN_PASSWORD` for an initial account or leave those two values blank and open `http://127.0.0.1:5000/setup` exactly once. Open `http://127.0.0.1:5000` after the app starts.

If activation is blocked, run `Set-ExecutionPolicy -Scope Process Bypass` and then activate the environment again. On the first start the official model files are downloaded into `models/`; if the machine is offline, copy the named `.onnx` files from the OpenCV Zoo into that directory and restart.

## Test

```powershell
python -m pytest -q
```

## Configuration

| Variable | Meaning |
|---|---|
| `SECRET_KEY` | Required Flask session signing key |
| `DATABASE_PATH` | SQLite database location relative to project root |
| `MODEL_DIR` | Local directory for the OpenCV ONNX files |
| `CAMERA_INDEX` | Camera index, normally `0` |
| `RECOGNITION_THRESHOLD` | Cosine score threshold, default `0.45` |
| `FLASK_DEBUG` | Set `true` only while developing |

## Privacy

The local face images, embeddings, database, CSV exports, logs, ONNX models, and `.env` are excluded from Git. Do not commit biometric data. For an organisational deployment, restrict host access, encrypt storage, provide consent/retention controls required by your jurisdiction, use HTTPS, and serve Flask through a production WSGI server.

## Architecture

`app.py` contains app setup and routes only. The `src/` package separates camera streaming, face detection/encoding/recognition, SQLite access, attendance, authentication, and utilities. Runtime folders and SQLite tables are created automatically at startup.

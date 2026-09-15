"""Flask entry point for the Face Recognition & Attendance Management System."""
import csv
import io
import logging
from pathlib import Path
import sqlite3
from flask import Flask, Response, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from config import BASE_DIR, Config
from src.attendance.attendance import AttendanceService
from src.camera.camera import Camera
from src.database.db import initialize_database
from src.database.models import Repository
from src.face.detector import FaceDetector
from src.face.encoder import FaceEncoder, ensure_models
from src.face.recognizer import FaceRecognizer
from src.face.registration import RegistrationService
from src.security.auth import hash_password, login_required, verify_password
from src.utils.helpers import decode_data_url, export_path
from src.utils.logger import configure_logging

LOGGER = logging.getLogger(__name__)


def create_app(test_config=None):
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    for directory in (BASE_DIR / "data/faces", BASE_DIR / "data/encodings", BASE_DIR / "database", BASE_DIR / "exports", BASE_DIR / "logs", app.config["MODEL_DIR"]):
        Path(directory).mkdir(parents=True, exist_ok=True)
    configure_logging(BASE_DIR / "logs")
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is required. Copy .env.example to .env and set it.")
    initialize_database(app.config["DATABASE_PATH"])
    repo = Repository(app.config["DATABASE_PATH"])
    if repo.admin_count() == 0 and app.config["ADMIN_USERNAME"] and app.config["ADMIN_PASSWORD"]:
        repo.create_admin(app.config["ADMIN_USERNAME"], hash_password(app.config["ADMIN_PASSWORD"]))
        LOGGER.info("Initial administrator created from environment configuration.")
    services = {"repo": repo, "camera": Camera(app.config["CAMERA_INDEX"]), "ready": False}
    try:
        models = ensure_models(app.config["MODEL_DIR"])
        detector = FaceDetector(models["face_detection_yunet_2023mar.onnx"])
        encoder = FaceEncoder(models["face_recognition_sface_2021dec.onnx"])
        services.update(detector=detector, encoder=encoder,
            registration=RegistrationService(detector, encoder, repo, BASE_DIR / "data/faces"),
            recognition=FaceRecognizer(repo, encoder, detector, app.config["RECOGNITION_THRESHOLD"]),
            attendance=AttendanceService(repo), ready=True)
    except Exception as exc:
        LOGGER.exception("Face services unavailable: %s", exc)
        services["model_error"] = str(exc)
    app.extensions["services"] = services

    @app.context_processor
    def context(): return {"camera_ready": services["ready"]}

    @app.get("/")
    def index(): return redirect(url_for("dashboard") if session.get("admin_id") else url_for("login"))

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if repo.admin_count(): return redirect(url_for("login"))
        if request.method == "POST":
            username, password = request.form.get("username", "").strip(), request.form.get("password", "")
            if len(username) < 3 or len(password) < 10:
                flash("Username must have 3 characters and password 10 characters.", "danger")
            else:
                repo.create_admin(username, hash_password(password)); flash("Administrator created. Please sign in.", "success")
                return redirect(url_for("login"))
        return render_template("login.html", setup=True)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            admin = repo.get_admin(request.form.get("username", "").strip())
            if admin and verify_password(admin["password_hash"], request.form.get("password", "")):
                session.clear(); session["admin_id"] = admin["id"]; session["admin_name"] = admin["username"]
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "danger")
        return render_template("login.html", setup=False, setup_needed=repo.admin_count() == 0)

    @app.post("/logout")
    @login_required
    def logout(): session.clear(); return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        total, today, recent = repo.dashboard_counts()
        return render_template("dashboard.html", total_users=total, today_count=today, recent=recent)

    @app.route("/register", methods=["GET", "POST"])
    @login_required
    def register():
        if request.method == "POST":
            try:
                employee_id = request.form.get("employee_id", "").strip()
                full_name = request.form.get("full_name", "").strip()
                if not employee_id or not full_name: raise ValueError("Employee ID and full name are required.")
                services["registration"].register(employee_id, full_name, request.form.get("department", "").strip(), request.form.get("email", "").strip(), decode_data_url(request.form.get("face_image", "")))
                flash(f"{full_name} was registered successfully.", "success"); return redirect(url_for("users"))
            except KeyError: flash("Face model is unavailable: " + services.get("model_error", "unknown error"), "danger")
            except (ValueError, sqlite3.IntegrityError) as exc: flash(str(exc) if isinstance(exc, ValueError) else "Employee ID already exists.", "danger")
            except Exception: LOGGER.exception("Registration failed"); flash("Registration failed. See application logs.", "danger")
        return render_template("register.html")

    @app.get("/recognition")
    @login_required
    def recognition(): return render_template("recognition.html")

    @app.post("/api/recognize")
    @login_required
    def recognize():
        if not services["ready"]: return jsonify(error=services.get("model_error", "Face services unavailable.")), 503
        try:
            import cv2, numpy as np
            image = cv2.imdecode(np.frombuffer(decode_data_url(request.json.get("image", "")), np.uint8), cv2.IMREAD_COLOR)
            result = services["recognition"].recognize(image)
            if result["status"] == "recognized":
                created, now = services["attendance"].record(result["user"]["id"], result["confidence"])
                result.update(message=(f"Welcome, {result['user']['full_name']}. Attendance recorded at {now:%H:%M}." if created else f"Welcome back, {result['user']['full_name']}. Attendance already recorded today."), attendance_recorded=created)
                result.pop("user")
            return jsonify(result)
        except Exception as exc:
            LOGGER.exception("Recognition failed")
            return jsonify(error=str(exc) if isinstance(exc, ValueError) else "Recognition could not be completed."), 400

    @app.get("/video-feed")
    @login_required
    def video_feed():
        if not services["ready"]: return Response(status=503)
        return Response(services["camera"].frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.get("/attendance")
    @login_required
    def attendance(): return render_template("attendance.html", records=repo.attendance(request.args.get("q", "").strip(), request.args.get("date", "")))

    @app.get("/attendance/export")
    @login_required
    def attendance_export():
        records = repo.attendance(request.args.get("q", "").strip(), request.args.get("date", ""))
        path = export_path(BASE_DIR / "exports")
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file); writer.writerow(["Date", "Check-in", "Employee ID", "Name", "Department", "Confidence"])
            writer.writerows([[r["attendance_date"], r["check_in"], r["employee_id"], r["full_name"], r["department"], r["confidence"]] for r in records])
        return send_file(path, as_attachment=True, download_name=path.name)

    @app.get("/users")
    @login_required
    def users(): return render_template("users.html", users=repo.list_users(request.args.get("q", "").strip()))

    @app.post("/users/<int:user_id>/toggle")
    @login_required
    def toggle_user(user_id):
        repo.set_user_active(user_id, request.form.get("active") == "1"); return redirect(url_for("users"))

    @app.errorhandler(404)
    def not_found(error): return render_template("error.html", message="The page you requested does not exist."), 404
    @app.errorhandler(500)
    def server_error(error): LOGGER.exception("Unhandled error"); return render_template("error.html", message="An unexpected server error occurred."), 500
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=Config.FLASK_DEBUG)

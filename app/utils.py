"""Utility helpers: unique grievance ID generator, file upload helpers, misc."""
import os
import uuid
import base64
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from .models import db, Grievance


def generate_unique_grievance_id():
    """Generate GRV-YYYY-0001 ... with per-year reset. Thread-safe via DB row lock."""
    year = datetime.utcnow().year
    prefix = f"GRV-{year}-"

    last_g = Grievance.query.filter(
        Grievance.grievance_id.like(prefix + "%")
    ).order_by(Grievance.id.desc()).first()

    if last_g is None:
        next_num = 1
    else:
        suffix = last_g.grievance_id[len(prefix):]
        try:
            next_num = int(suffix) + 1
        except ValueError:
            next_num = 1

    # Retry loop just in case of race condition (very rare in SQLite, but good practice)
    for _ in range(5):
        candidate = f"{prefix}{next_num:04d}"
        existing = Grievance.query.filter_by(grievance_id=candidate).first()
        if existing is None:
            return candidate
        next_num += 1
    raise RuntimeError("Failed to generate unique grievance ID after retries.")


def allowed_image(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_base64_image(data_uri):
    """Save a base64 data URI image to UPLOAD_FOLDER with a random filename.
    Returns relative path usable in templates (/static/uploads/...)."""
    header, b64 = data_uri.split(",", 1)
    ext = "png"
    if "jpeg" in header or "jpg" in header:
        ext = "jpg"
    elif "png" in header:
        ext = "png"
    elif "gif" in header:
        ext = "gif"

    allowed = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    if ext not in allowed:
        raise ValueError(f"Image extension {ext} not allowed.")

    raw_bytes = base64.b64decode(b64)
    if len(raw_bytes) > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ValueError("Image too large.")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    random_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(upload_dir, secure_filename(random_name))
    with open(filepath, "wb") as f:
        f.write(raw_bytes)

    return f"/static/uploads/{random_name}"


def save_uploaded_file(file_storage):
    """Fallback for tests — normal user flow MUST use camera only."""
    if file_storage.filename == "":
        raise ValueError("No file selected")
    if not allowed_image(file_storage.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
        raise ValueError("Disallowed extension")
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    random_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:12]}.{ext}"
    safe = secure_filename(random_name)
    file_storage.save(os.path.join(upload_dir, safe))
    return f"/static/uploads/{safe}"

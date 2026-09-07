"""Image handling utility functions"""
from pathlib import Path
from uuid import uuid4
from flask import abort
from werkzeug.utils import secure_filename

from utils.constants import ALLOWED_IMAGE_EXTENSIONS

def save_profile_picture(image):
    """
    profile picture changing file handling utiltiy
    """
    if not image or not image.filename:
        return None

    original_name = secure_filename(image.filename)
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        abort(400)

    filename = f"{uuid4().hex}{extension}"

    upload_dir = Path("static/uploads/users")
    upload_dir.mkdir(parents=True, exist_ok=True)

    image.save(upload_dir / filename)

    return filename

"""Store validated images and remove files after successful database changes."""
from pathlib import Path
from uuid import uuid4

from flask import current_app

from services import recipe_service


def upload_root():
    """Allow tests to isolate uploads from the application's static directory."""
    return Path(current_app.config.get("UPLOAD_FOLDER", "static/uploads"))


def save_profile_picture(image):
    """
        Save a previously validated optional profile upload.
        Args:
            image(Image): profile picture image
        Returns:
            filename(str): profile picture filename
    """
    if image is None or not image.filename:
        return None
    filename = f"{uuid4().hex}{Path(image.filename).suffix.lower()}"
    directory = upload_root() / "users"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    try:
        image.save(path)
    except OSError:
        path.unlink(missing_ok=True)
        raise
    return filename


def save_recipe_images(recipe_id, images, con, saved_files):
    """
        Track new files so a failed transaction can clean up every upload.
    """
    directory = upload_root() / "recipes" / str(recipe_id)
    for image in images:
        if not image.filename:
            continue
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}{Path(image.filename).suffix.lower()}"
        path = directory / filename
        saved_files.append(path)
        image.save(path)
        recipe_service.add_image(recipe_id, filename, con)


def remove_file(path):
    """
        Log cleanup failures without hiding an already committed database change.
        Args:
            path(str): filepath
    """
    try:
        path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.exception("Unable to remove image %s", path)


def remove_profile_file(filename):
    """
        Remove a stored profile picture if one exists.
        Args:
            filename(str): recipe filename
    """
    if filename:
        remove_file(upload_root() / "users" / Path(filename).name)


def remove_recipe_files(recipe_id, filenames):
    """
        Remove only the named files under this recipe's upload directory.
        Args:
            recipe_id(int): id of recipe
            filenames([]): recipe filenames
    """
    for filename in filenames:
        remove_file(upload_root() / "recipes" / str(recipe_id) / Path(filename).name)

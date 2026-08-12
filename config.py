import os


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-this"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///vellor_vine.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(
        "static",
        "uploads"
    )
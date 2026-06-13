import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "aml-secret-key")
    DATABASE_URL = os.environ.get("DATABASE_URL", str(BASE_DIR / "aml.db"))
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = str(BASE_DIR / "test_aml.db")


class ProductionConfig(Config):
    DEBUG = False

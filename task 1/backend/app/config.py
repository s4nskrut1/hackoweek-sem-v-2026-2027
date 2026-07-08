import os


class Config:
    """Central application configuration."""

    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # SQLite database stored inside backend/ directory
    SQLALCHEMY_DATABASE_URI = "sqlite:///lostlink.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JSON_SORT_KEYS = False

    # Simple admin key used to protect admin-only endpoints.
    # In a real production system this would be replaced by proper
    # authentication (JWT / session-based login).
    ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "admin123")

    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100 
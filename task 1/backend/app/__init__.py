from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db
from .utils.errors import register_error_handlers
from .routes import register_routes


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)  # Allow frontend (served separately) to call the API

    register_error_handlers(app)
    register_routes(app)

    with app.app_context():
        from .models import Item, Claim  # noqa: F401  (ensure models are registered)
        db.create_all()

    return app
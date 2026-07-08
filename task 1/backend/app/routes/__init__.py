from .items import items_bp
from .claims import claims_bp
from .admin import admin_bp


def register_routes(app):
    app.register_blueprint(items_bp, url_prefix="/api/items")
    app.register_blueprint(claims_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/")
    def index():
        return {
            "success": True,
            "message": "LostLink Campus API is running.",
            "version": "1.0.0",
        }, 200 
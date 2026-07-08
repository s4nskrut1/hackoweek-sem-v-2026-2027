from flask import jsonify


class APIError(Exception):
    """Custom exception carrying an HTTP status code and optional details."""

    def __init__(self, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def register_error_handlers(app):

    @app.errorhandler(APIError)
    def handle_api_error(err: APIError):
        payload = {"success": False, "error": err.message}
        if err.details:
            payload["details"] = err.details
        return jsonify(payload), err.status_code

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"success": False, "error": "Resource not found."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({"success": False, "error": "Method not allowed on this endpoint."}), 405

    @app.errorhandler(400)
    def handle_bad_request(err):
        return jsonify({"success": False, "error": "Malformed request."}), 400

    @app.errorhandler(500)
    def handle_server_error(err):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # Never leak internal exception details to the client
        if isinstance(err, APIError):
            return handle_api_error(err)
        app.logger.exception(err)
        return jsonify({"success": False, "error": "Something went wrong. Please try again."}), 500 
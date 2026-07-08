from flask import jsonify


def success_response(data=None, message: str = "Success", status_code: int = 200, meta: dict | None = None):
    """Standard success envelope used across all endpoints."""
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status_code 
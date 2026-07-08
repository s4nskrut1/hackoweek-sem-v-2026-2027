from functools import wraps

from flask import Blueprint, request, current_app

from ..models import Item, Claim
from ..utils.responses import success_response
from ..utils.errors import APIError

admin_bp = Blueprint("admin", __name__)


def require_admin(f):
    """Decorator protecting admin-only endpoints with a header-based key."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        admin_key = request.headers.get("X-Admin-Key")
        if not admin_key or admin_key != current_app.config["ADMIN_API_KEY"]:
            raise APIError("Unauthorized. A valid X-Admin-Key header is required.", 401)
        return f(*args, **kwargs)

    return wrapper


@admin_bp.route("/stats", methods=["GET"])
@require_admin
def get_stats():
    total_items = Item.query.count()
    lost_items = Item.query.filter_by(item_type="lost").count()
    found_items = Item.query.filter_by(item_type="found").count()
    active_items = Item.query.filter_by(status="active").count()
    claimed_items = Item.query.filter_by(status="claimed").count()
    returned_items = Item.query.filter_by(status="returned").count()

    total_claims = Claim.query.count()
    pending_claims = Claim.query.filter_by(status="pending").count()
    approved_claims = Claim.query.filter_by(status="approved").count()
    rejected_claims = Claim.query.filter_by(status="rejected").count()

    stats = {
        "items": {
            "total": total_items,
            "lost": lost_items,
            "found": found_items,
            "active": active_items,
            "claimed": claimed_items,
            "returned": returned_items,
        },
        "claims": {
            "total": total_claims,
            "pending": pending_claims,
            "approved": approved_claims,
            "rejected": rejected_claims,
        },
        "resolution_rate_percent": (
            round((returned_items / total_items) * 100, 2) if total_items else 0
        ),
    }
    return success_response(stats, "Statistics fetched successfully.") 
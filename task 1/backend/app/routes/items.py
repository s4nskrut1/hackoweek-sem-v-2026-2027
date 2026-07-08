from datetime import datetime

from flask import Blueprint, request

from ..extensions import db
from ..models import Item
from ..utils.responses import success_response
from ..utils.errors import APIError
from ..utils.validators import validate_item_payload
from ..utils.constants import CATEGORIES, LOCATIONS, ITEM_STATUSES
from .admin import require_admin

items_bp = Blueprint("items", __name__)


def get_item_or_404(item_id: int) -> Item:
    item = Item.query.get(item_id)
    if not item:
        raise APIError("Item not found.", 404)
    return item


def parse_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise APIError("Invalid date_occurred format. Use YYYY-MM-DD.", 422)


@items_bp.route("", methods=["POST"])
def report_item():
    """Report a lost or found item."""
    data = request.get_json(silent=True) or {}
    validate_item_payload(data)

    # Business rule: prevent duplicate reports of the same item by the same reporter
    duplicate = (
        Item.query.filter_by(
            item_type=data["item_type"],
            title=data["title"].strip(),
            category=data["category"],
            location=data["location"],
            reporter_email=data["reporter_email"].strip().lower(),
        )
        .filter(Item.status != "rejected")
        .first()
    )
    if duplicate:
        raise APIError(
            "A similar report already exists for this item. Duplicate reports are not allowed.",
            409,
        )

    date_occurred = parse_date(data["date_occurred"]) if data.get("date_occurred") else None

    item = Item(
        item_type=data["item_type"],
        title=data["title"].strip(),
        description=data["description"].strip(),
        category=data["category"],
        location=data["location"],
        reporter_name=data["reporter_name"].strip(),
        reporter_email=data["reporter_email"].strip().lower(),
        reporter_phone=data["reporter_phone"].strip(),
        date_occurred=date_occurred,
    )
    db.session.add(item)
    db.session.commit()

    return success_response(item.to_dict(), "Item reported successfully.", 201)


@items_bp.route("", methods=["GET"])
def list_items():
    """List items with optional search, filtering and pagination."""
    query = Item.query

    item_type = request.args.get("item_type")
    if item_type:
        if item_type not in ("lost", "found"):
            raise APIError("Invalid item_type filter. Must be 'lost' or 'found'.", 422)
        query = query.filter_by(item_type=item_type)

    category = request.args.get("category")
    if category:
        if category not in CATEGORIES:
            raise APIError(f"Invalid category filter. Must be one of {CATEGORIES}.", 422)
        query = query.filter_by(category=category)

    location = request.args.get("location")
    if location:
        if location not in LOCATIONS:
            raise APIError(f"Invalid location filter. Must be one of {LOCATIONS}.", 422)
        query = query.filter_by(location=location)

    status = request.args.get("status")
    if status:
        if status not in ITEM_STATUSES:
            raise APIError(f"Invalid status filter. Must be one of {ITEM_STATUSES}.", 422)
        query = query.filter_by(status=status)

    search = request.args.get("search")
    if search:
        like_pattern = f"%{search.strip()}%"
        query = query.filter(
            db.or_(Item.title.ilike(like_pattern), Item.description.ilike(like_pattern))
        )

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        raise APIError("page and per_page must be integers.", 422)

    if page < 1 or per_page < 1 or per_page > 100:
        raise APIError("Invalid pagination parameters.", 422)

    pagination = query.order_by(Item.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_items": pagination.total,
        "total_pages": pagination.pages,
    }

    return success_response(
        [item.to_dict() for item in pagination.items],
        "Items fetched successfully.",
        200,
        meta,
    )


@items_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = get_item_or_404(item_id)
    return success_response(item.to_dict(include_claims=True), "Item fetched successfully.")


@items_bp.route("/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Full update of an item. Not allowed once returned."""
    item = get_item_or_404(item_id)

    if item.status == "returned":
        raise APIError("Returned items cannot be edited.", 409)

    data = request.get_json(silent=True) or {}
    validate_item_payload(data)  # full payload required

    if data["item_type"] != item.item_type:
        raise APIError(
            "Item type cannot be changed once reported (e.g. a found item cannot become lost).",
            409,
        )

    item.title = data["title"].strip()
    item.description = data["description"].strip()
    item.category = data["category"]
    item.location = data["location"]
    item.reporter_name = data["reporter_name"].strip()
    item.reporter_email = data["reporter_email"].strip().lower()
    item.reporter_phone = data["reporter_phone"].strip()
    item.date_occurred = parse_date(data["date_occurred"]) if data.get("date_occurred") else None

    db.session.commit()
    return success_response(item.to_dict(), "Item updated successfully.")


@items_bp.route("/<int:item_id>", methods=["PATCH"])
def patch_item(item_id):
    """Partial update of an item. Not allowed once returned."""
    item = get_item_or_404(item_id)

    if item.status == "returned":
        raise APIError("Returned items cannot be edited.", 409)

    data = request.get_json(silent=True) or {}
    if not data:
        raise APIError("No fields provided to update.", 422)

    if "item_type" in data:
        raise APIError("Item type cannot be changed via partial update.", 409)

    validate_item_payload(data, partial=True)

    for field in ["title", "description", "category", "location", "reporter_name", "reporter_phone"]:
        if field in data:
            value = data[field]
            setattr(item, field, value.strip() if isinstance(value, str) else value)

    if "reporter_email" in data:
        item.reporter_email = data["reporter_email"].strip().lower()

    if "date_occurred" in data:
        item.date_occurred = parse_date(data["date_occurred"]) if data["date_occurred"] else None

    db.session.commit()
    return success_response(item.to_dict(), "Item updated successfully.")


@items_bp.route("/<int:item_id>", methods=["DELETE"])
@require_admin
def delete_item(item_id):
    """Admin-only: delete a fake or invalid report."""
    item = get_item_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return success_response(None, "Report deleted successfully.")


@items_bp.route("/<int:item_id>/return", methods=["PATCH"])
@require_admin
def mark_returned(item_id):
    """Admin-only: mark a claimed item as returned to its owner."""
    item = get_item_or_404(item_id)

    if item.status == "returned":
        raise APIError("Item is already marked as returned.", 409)

    if item.status != "claimed":
        raise APIError(
            "Only claimed items can be marked as returned. Approve a claim first.", 409
        )

    item.status = "returned"
    db.session.commit()
    return success_response(item.to_dict(), "Item marked as returned successfully.") 
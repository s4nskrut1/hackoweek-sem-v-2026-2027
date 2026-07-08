from flask import Blueprint, request

from ..extensions import db
from ..models import Item, Claim
from ..utils.responses import success_response
from ..utils.errors import APIError
from ..utils.validators import validate_claim_payload
from .admin import require_admin

claims_bp = Blueprint("claims", __name__)


def get_claim_or_404(claim_id: int) -> Claim:
    claim = Claim.query.get(claim_id)
    if not claim:
        raise APIError("Claim not found.", 404)
    return claim


@claims_bp.route("/items/<int:item_id>/claims", methods=["POST"])
def submit_claim(item_id):
    """Submit a claim request for a found item."""
    item = Item.query.get(item_id)
    if not item:
        raise APIError("Item not found.", 404)

    if item.item_type != "found":
        raise APIError("Claims can only be submitted for items reported as found.", 409)

    if item.status == "returned":
        raise APIError("This item has already been returned to its owner.", 409)

    if item.status == "claimed":
        raise APIError("This item has already been claimed.", 409)

    data = request.get_json(silent=True) or {}
    validate_claim_payload(data)

    claimant_email = data["claimant_email"].strip().lower()

    # Business rule: same person cannot submit a duplicate pending claim
    existing = Claim.query.filter_by(
        item_id=item_id, claimant_email=claimant_email, status="pending"
    ).first()
    if existing:
        raise APIError(
            "You already have a pending claim on this item. Please wait for it to be reviewed.",
            409,
        )

    claim = Claim(
        item_id=item_id,
        claimant_name=data["claimant_name"].strip(),
        claimant_email=claimant_email,
        claimant_phone=data["claimant_phone"].strip(),
        proof_description=data["proof_description"].strip(),
    )
    db.session.add(claim)
    db.session.commit()

    return success_response(claim.to_dict(), "Claim submitted successfully. Awaiting review.", 201)


@claims_bp.route("/items/<int:item_id>/claims", methods=["GET"])
def list_item_claims(item_id):
    item = Item.query.get(item_id)
    if not item:
        raise APIError("Item not found.", 404)

    claims = Claim.query.filter_by(item_id=item_id).order_by(Claim.created_at.desc()).all()
    return success_response([c.to_dict() for c in claims], "Claims fetched successfully.")


@claims_bp.route("/claims/<int:claim_id>", methods=["GET"])
def track_claim(claim_id):
    """Students track the status of their claim by ID."""
    claim = get_claim_or_404(claim_id)
    return success_response(claim.to_dict(), "Claim status fetched successfully.")


@claims_bp.route("/claims/<int:claim_id>/approve", methods=["PATCH"])
@require_admin
def approve_claim(claim_id):
    claim = get_claim_or_404(claim_id)

    if claim.status == "approved":
        raise APIError("This claim has already been approved.", 409)
    if claim.status == "rejected":
        raise APIError("A rejected claim cannot be approved.", 409)

    item = Item.query.get(claim.item_id)
    if item.status == "claimed":
        raise APIError("This item has already been claimed through another request.", 409)
    if item.status == "returned":
        raise APIError("This item has already been returned.", 409)

    claim.status = "approved"
    item.status = "claimed"

    # Business rule: auto-reject all other pending claims for the same item
    other_pending_claims = Claim.query.filter(
        Claim.item_id == item.id, Claim.id != claim.id, Claim.status == "pending"
    ).all()
    for other_claim in other_pending_claims:
        other_claim.status = "rejected"

    db.session.commit()
    return success_response(claim.to_dict(), "Claim approved. Item marked as claimed.")


@claims_bp.route("/claims/<int:claim_id>/reject", methods=["PATCH"])
@require_admin
def reject_claim(claim_id):
    claim = get_claim_or_404(claim_id)

    if claim.status == "rejected":
        raise APIError("This claim has already been rejected.", 409)
    if claim.status == "approved":
        raise APIError("An approved claim cannot be rejected.", 409)

    claim.status = "rejected"
    db.session.commit()
    return success_response(claim.to_dict(), "Claim rejected successfully.") 
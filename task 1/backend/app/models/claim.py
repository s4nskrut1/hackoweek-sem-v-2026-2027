from datetime import datetime
from ..extensions import db


class Claim(db.Model):
    """
    Represents a claim submitted by a student for a found item.

    status: 'pending' | 'approved' | 'rejected'
    """

    __tablename__ = "claims"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)

    claimant_name = db.Column(db.String(100), nullable=False)
    claimant_email = db.Column(db.String(120), nullable=False)
    claimant_phone = db.Column(db.String(20), nullable=False)
    proof_description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), nullable=False, default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "claimant_name": self.claimant_name,
            "claimant_email": self.claimant_email,
            "claimant_phone": self.claimant_phone,
            "proof_description": self.proof_description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        } 
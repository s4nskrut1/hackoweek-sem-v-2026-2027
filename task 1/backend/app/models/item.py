from datetime import datetime
from ..extensions import db


class Item(db.Model):
    """
    Represents a lost or found item reported by a student.

    item_type: 'lost' | 'found'
    status:    'active' | 'claimed' | 'returned' | 'rejected'
    """

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)

    item_type = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")

    reporter_name = db.Column(db.String(100), nullable=False)
    reporter_email = db.Column(db.String(120), nullable=False)
    reporter_phone = db.Column(db.String(20), nullable=False)

    date_occurred = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    claims = db.relationship(
        "Claim", backref="item", cascade="all, delete-orphan", lazy=True
    )

    def to_dict(self, include_claims: bool = False) -> dict:
        data = {
            "id": self.id,
            "item_type": self.item_type,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "location": self.location,
            "status": self.status,
            "reporter_name": self.reporter_name,
            "reporter_email": self.reporter_email,
            "reporter_phone": self.reporter_phone,
            "date_occurred": self.date_occurred.isoformat() if self.date_occurred else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active_claims_count": sum(
                1 for c in self.claims if c.status in ("pending", "approved")
            ),
        }
        if include_claims:
            data["claims"] = [c.to_dict() for c in self.claims]
        return data 
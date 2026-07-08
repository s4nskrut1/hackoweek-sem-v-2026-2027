import re

from .constants import CATEGORIES, LOCATIONS, ITEM_TYPES
from .errors import APIError

EMAIL_REGEX = re.compile(r"^[\w\.\-+]+@[\w\-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\d{10}$")


def validate_email(email: str):
    if not email or not EMAIL_REGEX.match(email.strip()):
        raise APIError("Invalid email address.", 422)


def validate_phone(phone: str):
    if not phone or not PHONE_REGEX.match(phone.strip()):
        raise APIError("Invalid phone number. Must be exactly 10 digits.", 422)


def require_fields(data: dict, fields: list[str]):
    missing = [f for f in fields if str(data.get(f, "")).strip() == ""]
    if missing:
        raise APIError(
            "Missing required fields.", 422, details={"missing_fields": missing}
        )


def validate_item_payload(data: dict, partial: bool = False):
    """Validates payload for creating (full) or patching (partial) an item."""
    required = [
        "item_type", "title", "description", "category",
        "location", "reporter_name", "reporter_email", "reporter_phone",
    ]
    if not partial:
        require_fields(data, required)

    if "item_type" in data and data["item_type"] not in ITEM_TYPES:
        raise APIError(f"Invalid item_type. Must be one of {ITEM_TYPES}.", 422)

    if "category" in data and data["category"] not in CATEGORIES:
        raise APIError(f"Invalid category. Must be one of {CATEGORIES}.", 422)

    if "location" in data and data["location"] not in LOCATIONS:
        raise APIError(f"Invalid location. Must be one of {LOCATIONS}.", 422)

    if "reporter_email" in data:
        validate_email(data["reporter_email"])

    if "reporter_phone" in data:
        validate_phone(data["reporter_phone"])

    if "title" in data and len(str(data["title"]).strip()) < 3:
        raise APIError("Title must be at least 3 characters long.", 422)

    if "description" in data and len(str(data["description"]).strip()) < 10:
        raise APIError("Description must be at least 10 characters long.", 422)


def validate_claim_payload(data: dict):
    required = ["claimant_name", "claimant_email", "claimant_phone", "proof_description"]
    require_fields(data, required)

    validate_email(data["claimant_email"])
    validate_phone(data["claimant_phone"])

    if len(str(data["proof_description"]).strip()) < 15:
        raise APIError(
            "Proof description must be at least 15 characters long to help verify ownership.",
            422,
        ) 
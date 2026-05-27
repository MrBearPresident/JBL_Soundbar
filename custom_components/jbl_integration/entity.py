"""Shared entity helpers for the JBL integration."""

from homeassistant.util import slugify


def entity_id_slug(value: str) -> str:
    """Return a Home Assistant-safe slug for manual entity IDs."""
    return slugify(value).replace("-", "_")


def build_entity_id(platform: str, *parts: str) -> str:
    """Build a sanitized entity ID from a platform and name parts."""
    return f"{platform}.{ '_'.join(entity_id_slug(part) for part in parts if part) }"
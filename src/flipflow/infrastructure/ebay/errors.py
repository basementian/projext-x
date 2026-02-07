"""eBay API error response parsing utilities."""

import httpx

from flipflow.core.exceptions import DuplicateListingError


def parse_error_response(response: httpx.Response) -> dict:
    """Extract structured error info from an eBay error response."""
    try:
        body = response.json()
        errors = body.get("errors", [])
        if errors:
            first = errors[0]
            return {
                "error_id": first.get("errorId", 0),
                "message": first.get("message", "Unknown error"),
                "category": first.get("category", "APPLICATION"),
                "domain": first.get("domain", ""),
            }
    except Exception:
        pass
    return {
        "error_id": 0,
        "message": response.text,
        "category": "APPLICATION",
        "domain": "",
    }


def raise_for_inventory_error(response: httpx.Response) -> None:
    """Raise domain-specific exceptions for inventory API errors."""
    if response.status_code < 400:
        return
    info = parse_error_response(response)
    if info["error_id"] == 25002:
        raise DuplicateListingError(info["message"])

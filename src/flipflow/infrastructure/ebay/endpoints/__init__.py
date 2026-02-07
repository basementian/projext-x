"""eBay API endpoint modules."""

from flipflow.infrastructure.ebay.endpoints.account import AccountEndpoints
from flipflow.infrastructure.ebay.endpoints.analytics import AnalyticsEndpoints
from flipflow.infrastructure.ebay.endpoints.browse import BrowseEndpoints
from flipflow.infrastructure.ebay.endpoints.inventory import InventoryEndpoints
from flipflow.infrastructure.ebay.endpoints.marketing import MarketingEndpoints
from flipflow.infrastructure.ebay.endpoints.negotiation import NegotiationEndpoints
from flipflow.infrastructure.ebay.endpoints.offers import OfferEndpoints

__all__ = [
    "AccountEndpoints",
    "AnalyticsEndpoints",
    "BrowseEndpoints",
    "InventoryEndpoints",
    "MarketingEndpoints",
    "NegotiationEndpoints",
    "OfferEndpoints",
]

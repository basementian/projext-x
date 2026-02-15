"""Custom exception hierarchy for FlipFlow."""


class FlipFlowError(Exception):
    """Base exception for all FlipFlow errors."""


class GatekeeperError(FlipFlowError):
    """Base for input validation errors."""


class LowSTRError(GatekeeperError):
    """Listing blocked due to low Sell-Through Rate."""

    def __init__(self, str_value: float, threshold: float = 0.4):
        self.str_value = str_value
        self.threshold = threshold
        super().__init__(f"Sell-Through Rate {str_value:.1%} is below minimum {threshold:.0%}")


class LowProfitError(GatekeeperError):
    """Listing would result in below-floor profit."""

    def __init__(self, net_profit: float, floor: float = 5.00):
        self.net_profit = net_profit
        self.floor = floor
        super().__init__(f"Net profit ${net_profit:.2f} is below minimum ${floor:.2f}")


class TitleError(GatekeeperError):
    """Title validation failed."""


class LifecycleError(FlipFlowError):
    """Base for lifecycle management errors."""


class ZombieDetectionError(LifecycleError):
    """Error during zombie scanning."""


class ResurrectionError(LifecycleError):
    """Error during listing resurrection."""


class ResurrectionCooldownError(ResurrectionError):
    """Tried to relist too quickly after ending."""


class QueueError(LifecycleError):
    """Error in SmartQueue operations."""


class EbayError(FlipFlowError):
    """Base for eBay API errors."""


class EbayAuthError(EbayError):
    """Authentication/token error."""


class EbayRateLimitError(EbayError):
    """API rate limit exceeded."""


class EbayNotFoundError(EbayError):
    """Requested resource not found on eBay."""


class DuplicateListingError(EbayError):
    """eBay rejected listing as duplicate."""

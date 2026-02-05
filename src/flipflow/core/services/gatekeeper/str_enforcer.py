"""STR Enforcer — blocks listings with low Sell-Through Rate.

Research: Listings with <40% STR are mathematically destined to fail.
Prevents "death pile" accumulation.

CAVEAT: eBay's Marketplace Insights API is restricted to approved partners.
MVP supports manual STR input from Terapeak/Seller Hub. Future versions
can integrate the API if access is granted.

Three modes:
- "manual": seller inputs STR from Terapeak (MVP)
- "api": future Marketplace Insights API integration
- "estimated": rough proxy from Browse API active/sold ratio
"""

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import STRSource
from flipflow.core.exceptions import LowSTRError


class STREnforcer:
    """Validates listings against Sell-Through Rate thresholds."""

    DEFAULT_THRESHOLD = 0.4  # 40% minimum STR

    def __init__(self, config: FlipFlowConfig):
        self.threshold = self.DEFAULT_THRESHOLD

    def validate_manual(self, str_value: float, allow_override: bool = False) -> dict:
        """Validate a manually-entered STR value.

        Args:
            str_value: Sell-through rate as a decimal (0.0 to 1.0)
            allow_override: If True, returns a warning instead of blocking

        Returns:
            dict with 'approved', 'str_value', 'threshold', and optional 'warning'

        Raises:
            LowSTRError: If STR is below threshold and override not allowed
        """
        if str_value < 0 or str_value > 1:
            raise ValueError(f"STR must be between 0 and 1, got {str_value}")

        passes = str_value >= self.threshold

        if not passes and not allow_override:
            raise LowSTRError(str_value, self.threshold)

        result = {
            "approved": passes or allow_override,
            "str_value": str_value,
            "threshold": self.threshold,
            "source": STRSource.MANUAL,
            "passes_threshold": passes,
        }

        if not passes and allow_override:
            result["warning"] = (
                f"STR {str_value:.1%} is below {self.threshold:.0%} threshold. "
                "Listing approved via High Margin Exception override."
            )

        return result

    def calculate_str(self, sold_count: int, active_count: int) -> float:
        """Calculate sell-through rate from sold and active counts.

        STR = sold / (sold + active)
        """
        total = sold_count + active_count
        if total == 0:
            return 0.0
        return sold_count / total

    async def validate_from_api(self, query: str) -> dict:
        """Validate STR using eBay API data.

        NOT IMPLEMENTED in MVP — Marketplace Insights API requires
        approved partner access.
        """
        raise NotImplementedError(
            "eBay Marketplace Insights API access is restricted to approved partners. "
            "Use validate_manual() with data from Terapeak/Seller Hub instead."
        )

"""Tests for Profit Floor Calculator."""

import math

import pytest

from flipflow.core.config import FlipFlowConfig
from flipflow.core.schemas.profit import ProfitCalcRequest
from flipflow.core.services.gatekeeper.profit_floor import ProfitFloorCalc


@pytest.fixture
def calc() -> ProfitFloorCalc:
    config = FlipFlowConfig(_env_file=None)
    return ProfitFloorCalc(config)


class TestProfitCalculation:
    def test_basic_profitable_item(self, calc):
        """$50 item bought at $10 should be profitable."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=50,
                purchase_price=10,
                shipping_cost=5,
            )
        )
        assert result.net_profit > 0
        assert result.meets_floor is True

    def test_fee_breakdown_matches_total(self, calc):
        """Individual fees should sum to total_fees."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=100,
                purchase_price=30,
                shipping_cost=10,
                ad_rate_percent=1.5,
            )
        )
        expected_total = (
            result.ebay_fee_amount + result.ad_fee_amount + result.payment_processing_amount
        )
        assert abs(result.total_fees - expected_total) < 0.02

    def test_net_profit_formula(self, calc):
        """net = sale - cost - shipping - fees."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=80,
                purchase_price=20,
                shipping_cost=8,
            )
        )
        expected = 80 - 20 - 8 - result.total_fees
        assert abs(result.net_profit - expected) < 0.02

    def test_ebay_fee_is_13_percent(self, calc):
        """Default eBay fee should be 13% of sale price."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=100,
                purchase_price=10,
            )
        )
        assert result.ebay_fee_amount == 13.00

    def test_ad_fee_calculation(self, calc):
        """Ad fee at 1.5% on $100 = $1.50."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=100,
                purchase_price=10,
                ad_rate_percent=1.5,
            )
        )
        assert result.ad_fee_amount == 1.50

    def test_zero_ad_rate(self, calc):
        """No ads means no ad fee."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=50,
                purchase_price=10,
            )
        )
        assert result.ad_fee_amount == 0.0

    def test_below_floor_warning(self, calc):
        """Item with thin margins should fail floor check."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=15,
                purchase_price=10,
                shipping_cost=2,
            )
        )
        assert result.meets_floor is False
        assert result.net_profit < 5.00

    def test_exactly_at_floor(self, calc):
        """Profit exactly at floor should pass."""
        # Find the exact price that hits $5 floor
        min_price = calc.find_minimum_price(10, 5, 0)
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=min_price,
                purchase_price=10,
                shipping_cost=5,
            )
        )
        assert result.meets_floor is True
        assert abs(result.net_profit - 5.00) < 0.02

    def test_zero_purchase_price_freebie(self, calc):
        """Free items (found/gifted) should have high margins."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=20,
                purchase_price=0,
            )
        )
        assert result.net_profit > 10
        assert result.profit_margin_percent > 50

    def test_high_ad_rate_eats_profit(self, calc):
        """Excessive ad rate should destroy profitability."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=30,
                purchase_price=15,
                shipping_cost=5,
                ad_rate_percent=10,
            )
        )
        assert result.meets_floor is False

    def test_profit_margin_percentage(self, calc):
        """Margin should be net_profit / sale_price * 100."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=100,
                purchase_price=20,
            )
        )
        expected_margin = result.net_profit / 100 * 100
        assert abs(result.profit_margin_percent - expected_margin) < 0.1

    def test_payment_processing_includes_flat_fee(self, calc):
        """Payment processing = sale * rate + per_order_fee."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=100,
                purchase_price=10,
            )
        )
        expected = 100 * 0.029 + 0.30
        assert abs(result.payment_processing_amount - expected) < 0.01


class TestMinimumViablePrice:
    def test_minimum_price_achieves_floor(self, calc):
        """Min price should result in exactly $5 profit."""
        min_price = calc.find_minimum_price(20, 5, 0)
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=min_price,
                purchase_price=20,
                shipping_cost=5,
            )
        )
        assert abs(result.net_profit - 5.00) < 0.02

    def test_minimum_price_with_ads(self, calc):
        """Min price should account for ad costs."""
        min_no_ads = calc.find_minimum_price(20, 5, 0)
        min_with_ads = calc.find_minimum_price(20, 5, 2.0)
        assert min_with_ads > min_no_ads

    def test_minimum_price_zero_cost(self, calc):
        """Free items still have fees to overcome."""
        min_price = calc.find_minimum_price(0, 0, 0)
        assert min_price > 5.00  # Must cover floor + fees

    def test_impossible_fee_rate_returns_inf(self, calc):
        """If fees exceed 100%, return infinity."""
        result = calc.find_minimum_price(10, 5, 90)  # 90% ad + 13% base + 2.9% payment > 100%
        assert math.isinf(result)

    def test_minimum_price_increases_with_cost(self, calc):
        """Higher purchase cost → higher minimum price."""
        min_cheap = calc.find_minimum_price(5, 0, 0)
        min_expensive = calc.find_minimum_price(50, 0, 0)
        assert min_expensive > min_cheap

    def test_response_includes_minimum_price(self, calc):
        """Calculate response should include minimum_viable_price."""
        result = calc.calculate(
            ProfitCalcRequest(
                sale_price=50,
                purchase_price=20,
                shipping_cost=5,
            )
        )
        assert result.minimum_viable_price > 0

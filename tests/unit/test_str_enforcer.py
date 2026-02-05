"""Tests for STR Enforcer — Sell-Through Rate validation."""

import pytest

from flipflow.core.config import FlipFlowConfig
from flipflow.core.exceptions import LowSTRError
from flipflow.core.services.gatekeeper.str_enforcer import STREnforcer


@pytest.fixture
def enforcer(test_config):
    return STREnforcer(test_config)


class TestManualValidation:
    def test_high_str_passes(self, enforcer):
        result = enforcer.validate_manual(0.65)
        assert result["approved"] is True
        assert result["passes_threshold"] is True

    def test_exactly_at_threshold_passes(self, enforcer):
        result = enforcer.validate_manual(0.4)
        assert result["approved"] is True

    def test_low_str_blocks(self, enforcer):
        with pytest.raises(LowSTRError) as exc_info:
            enforcer.validate_manual(0.25)
        assert exc_info.value.str_value == 0.25
        assert exc_info.value.threshold == 0.4

    def test_low_str_with_override(self, enforcer):
        result = enforcer.validate_manual(0.25, allow_override=True)
        assert result["approved"] is True
        assert result["passes_threshold"] is False
        assert "warning" in result
        assert "High Margin Exception" in result["warning"]

    def test_zero_str_blocks(self, enforcer):
        with pytest.raises(LowSTRError):
            enforcer.validate_manual(0.0)

    def test_perfect_str_passes(self, enforcer):
        result = enforcer.validate_manual(1.0)
        assert result["approved"] is True

    def test_invalid_str_over_1(self, enforcer):
        with pytest.raises(ValueError, match="between 0 and 1"):
            enforcer.validate_manual(1.5)

    def test_invalid_str_negative(self, enforcer):
        with pytest.raises(ValueError, match="between 0 and 1"):
            enforcer.validate_manual(-0.1)

    def test_source_is_manual(self, enforcer):
        result = enforcer.validate_manual(0.5)
        assert result["source"] == "manual"


class TestSTRCalculation:
    def test_basic_calculation(self, enforcer):
        # 60 sold, 40 active = 60%
        assert enforcer.calculate_str(60, 40) == 0.6

    def test_zero_sold(self, enforcer):
        assert enforcer.calculate_str(0, 100) == 0.0

    def test_all_sold(self, enforcer):
        assert enforcer.calculate_str(100, 0) == 1.0

    def test_zero_both(self, enforcer):
        assert enforcer.calculate_str(0, 0) == 0.0

    def test_realistic_numbers(self, enforcer):
        # 30 sold, 45 active = 40%
        result = enforcer.calculate_str(30, 45)
        assert abs(result - 0.4) < 0.01


class TestAPIValidation:
    async def test_api_raises_not_implemented(self, enforcer):
        with pytest.raises(NotImplementedError, match="approved partners"):
            await enforcer.validate_from_api("nike air max")

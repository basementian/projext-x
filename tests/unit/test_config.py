"""Test FlipFlow configuration loading."""

from flipflow.core.config import FlipFlowConfig


def test_config_loads_defaults():
    """Config should load with sensible defaults."""
    config = FlipFlowConfig(
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )
    assert config.ebay_mode == "mock"
    assert config.ebay_base_fee_rate == 0.13
    assert config.min_profit_floor == 5.00
    assert config.zombie_days_threshold == 60
    assert config.zombie_views_threshold == 10
    assert config.max_zombie_cycles == 3
    assert config.queue_batch_size == 10
    assert config.surge_window_day == "sunday"
    assert config.surge_window_start_hour == 20
    assert config.surge_window_end_hour == 22


def test_config_fee_rates():
    """Fee rates should be reasonable."""
    config = FlipFlowConfig(_env_file=None)
    assert 0 < config.ebay_base_fee_rate < 1
    assert 0 < config.payment_processing_rate < 1
    assert config.per_order_fee >= 0


def test_config_mock_mode_no_keys_needed():
    """In mock mode, empty eBay credentials are fine."""
    config = FlipFlowConfig(ebay_mode="mock", _env_file=None)
    assert config.ebay_client_id == ""
    assert config.ebay_client_secret == ""

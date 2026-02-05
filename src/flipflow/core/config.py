"""FlipFlow configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class FlipFlowConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLIPFLOW_", env_file=".env")

    # Database
    database_url: str = "sqlite+aiosqlite:///./flipflow.db"

    # eBay
    ebay_mode: str = "mock"  # "mock" | "sandbox" | "production"
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_redirect_uri: str = ""
    ebay_refresh_token: str = ""

    # Fee structure
    ebay_base_fee_rate: float = 0.13
    payment_processing_rate: float = 0.029
    per_order_fee: float = 0.30
    min_profit_floor: float = 5.00

    # Zombie detection
    zombie_days_threshold: int = 60
    zombie_views_threshold: int = 10
    max_zombie_cycles: int = 3
    resurrection_delay_seconds: int = 120

    # SmartQueue
    queue_batch_size: int = 10
    surge_window_day: str = "sunday"
    surge_window_start_hour: int = 20
    surge_window_end_hour: int = 22
    surge_window_timezone: str = "America/New_York"

    # Kickstarter
    kickstarter_ad_rate: float = 1.5
    kickstarter_duration_days: int = 14

    # Offer Sniper
    offer_discount_percent: float = 10.0
    offer_poll_interval_hours: int = 1

    # Purgatory
    purgatory_sale_percent: float = 30.0

    # Photo Shuffler
    photo_shuffle_days_no_views: int = 14

    # Store Pulse
    store_pulse_day_of_month: int = 1

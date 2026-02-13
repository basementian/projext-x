"""Magic numbers, thresholds, and static values used across FlipFlow."""

# eBay fee structure defaults
EBAY_BASE_FEE_RATE = 0.13
PAYMENT_PROCESSING_RATE = 0.029
PER_ORDER_FEE = 0.30
DEFAULT_MIN_PROFIT = 5.00

# Listing constraints
MAX_TITLE_LENGTH = 80
BRAND_MODEL_TARGET_POSITION = 30

# Zombie detection
DEFAULT_ZOMBIE_DAYS = 60
DEFAULT_ZOMBIE_VIEWS = 10
MAX_ZOMBIE_CYCLES_DEFAULT = 3

# Resurrector
RESURRECTION_COOLDOWN_SECONDS = 120

# SmartQueue
DEFAULT_BATCH_SIZE = 10
SURGE_WINDOW = {
    "day": "sunday",
    "start_hour": 20,
    "end_hour": 22,
    "timezone": "America/New_York",
}

# Kickstarter (Promoted Listings)
DEFAULT_AD_RATE = 1.5
KICKSTARTER_DURATION_DAYS = 14


class ListingStatus:
    DRAFT = "draft"
    QUEUED = "queued"
    ACTIVE = "active"
    ZOMBIE = "zombie"
    PURGATORY = "purgatory"
    SOLD = "sold"
    ENDED = "ended"


class ZombieAction:
    FLAGGED = "flagged"
    RESURRECTED = "resurrected"
    PURGATORED = "purgatored"


class QueueStatus:
    PENDING = "pending"
    RELEASED = "released"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CampaignType:
    KICKSTARTER = "kickstarter"
    MANUAL = "manual"


class CampaignStatus:
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class JobStatus:
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class STRSource:
    MANUAL = "manual"
    API = "api"
    ESTIMATED = "estimated"


class RelistAction:
    PREVENTIVE_RELIST = "preventive_relist"


class OfferStatus:
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class OfferAction:
    ACCEPT = "accept"
    COUNTER = "counter"
    REJECT = "reject"

"""Listings API — CRUD with gatekeeper validation."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.api.dependencies import get_config, get_db
from flipflow.core.config import FlipFlowConfig
from flipflow.core.models.listing import Listing
from flipflow.core.schemas.profit import ProfitCalcRequest
from flipflow.core.schemas.title import TitleSanitizeRequest
from flipflow.core.services.gatekeeper.profit_floor import ProfitFloorCalc
from flipflow.core.services.gatekeeper.title_sanitizer import TitleSanitizer

router = APIRouter()


class ListingCreate(BaseModel):
    sku: str
    title: str
    purchase_price: float = Field(ge=0)
    list_price: float = Field(gt=0)
    shipping_cost: float = Field(ge=0, default=0)
    brand: str | None = None
    model: str | None = None
    description: str = ""


class ListingResponse(BaseModel):
    id: int
    sku: str
    title: str
    title_sanitized: str | None
    status: str
    purchase_price: float
    list_price: float
    days_active: int
    total_views: int
    zombie_cycle_count: int


@router.get("/listings")
async def list_listings(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Listing)
    if status:
        stmt = stmt.where(Listing.status == status)
    result = await db.execute(stmt)
    listings = result.scalars().all()
    return [
        ListingResponse(
            id=l.id,
            sku=l.sku,
            title=l.title,
            title_sanitized=l.title_sanitized,
            status=l.status,
            purchase_price=float(l.purchase_price),
            list_price=float(l.list_price),
            days_active=l.days_active,
            total_views=l.total_views,
            zombie_cycle_count=l.zombie_cycle_count,
        )
        for l in listings
    ]


@router.post("/listings", status_code=201)
async def create_listing(
    data: ListingCreate,
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
):
    # Auto-sanitize title
    sanitizer = TitleSanitizer()
    sanitized = sanitizer.sanitize(
        TitleSanitizeRequest(
            title=data.title,
            brand=data.brand,
            model=data.model,
        )
    )

    # Auto-calculate profit
    calc = ProfitFloorCalc(config)
    profit = calc.calculate(
        ProfitCalcRequest(
            sale_price=data.list_price,
            purchase_price=data.purchase_price,
            shipping_cost=data.shipping_cost,
        )
    )

    listing = Listing(
        sku=data.sku,
        title=data.title,
        title_sanitized=sanitized.sanitized,
        description=data.description,
        purchase_price=data.purchase_price,
        list_price=data.list_price,
        shipping_cost=data.shipping_cost,
        brand=data.brand,
        model=data.model,
    )
    db.add(listing)
    await db.flush()

    return {
        "id": listing.id,
        "sku": listing.sku,
        "title_sanitized": sanitized.sanitized,
        "title_changes": sanitized.changes,
        "profit": {
            "net_profit": profit.net_profit,
            "meets_floor": profit.meets_floor,
            "minimum_viable_price": profit.minimum_viable_price,
        },
    }


@router.get("/listings/{listing_id}")
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    listing = await db.get(Listing, listing_id)
    if listing is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingResponse(
        id=listing.id,
        sku=listing.sku,
        title=listing.title,
        title_sanitized=listing.title_sanitized,
        status=listing.status,
        purchase_price=float(listing.purchase_price),
        list_price=float(listing.list_price),
        days_active=listing.days_active,
        total_views=listing.total_views,
        zombie_cycle_count=listing.zombie_cycle_count,
    )

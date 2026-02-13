"""Offers API — tiered offer handling endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.api.dependencies import get_config, get_db, get_ebay
from flipflow.core.config import FlipFlowConfig
from flipflow.core.services.growth.offer_sniper import OfferSniper

router = APIRouter()


class IncomingOfferRequest(BaseModel):
    buyer_id: str
    offer_id: str
    offer_amount: float


@router.post("/offers/scan")
async def scan_and_snipe(
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    sniper = OfferSniper(ebay, config)
    return await sniper.scan_and_snipe(db)


@router.post("/offers/{listing_id}/handle")
async def handle_incoming_offer(
    listing_id: int,
    request: IncomingOfferRequest,
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    sniper = OfferSniper(ebay, config)
    return await sniper.handle_incoming_offer(
        db, listing_id, request.buyer_id, request.offer_id, request.offer_amount,
    )

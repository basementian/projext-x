"""Zombies API — detection and resurrection endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.api.dependencies import get_db, get_config, get_ebay
from flipflow.core.config import FlipFlowConfig
from flipflow.core.services.lifecycle.zombie_killer import ZombieKiller
from flipflow.core.services.lifecycle.resurrector import Resurrector

router = APIRouter()


@router.get("/zombies")
async def scan_zombies(
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    killer = ZombieKiller(ebay, config)
    result = await killer.scan(db)
    return result.model_dump()


@router.post("/zombies/{listing_id}/resurrect")
async def resurrect_zombie(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    resurrector = Resurrector(ebay, config)
    result = await resurrector.resurrect(db, listing_id)
    return result.model_dump()

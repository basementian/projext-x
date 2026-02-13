"""Repricer API — graduated markdown ladder endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.api.dependencies import get_db, get_config, get_ebay
from flipflow.core.config import FlipFlowConfig
from flipflow.core.services.lifecycle.repricer import Repricer

router = APIRouter()


@router.get("/repricer/preview")
async def preview_repricing(
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    repricer = Repricer(ebay, config)
    result = await repricer.scan_and_reprice(db)
    # Preview returns the details without pushing to eBay
    return result


@router.post("/repricer/run")
async def run_repricing(
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    repricer = Repricer(ebay, config)
    return await repricer.scan_and_reprice(db)

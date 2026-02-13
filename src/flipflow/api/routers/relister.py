"""Auto Relister API — proactive scheduled relisting endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.api.dependencies import get_config, get_db, get_ebay
from flipflow.core.config import FlipFlowConfig
from flipflow.core.services.lifecycle.auto_relister import AutoRelister

router = APIRouter()


@router.get("/relister/preview")
async def preview_relists(
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    relister = AutoRelister(ebay, config)
    return await relister.scan_for_relists(db)


@router.post("/relister/run")
async def run_relists(
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    relister = AutoRelister(ebay, config)
    return await relister.auto_relist(db)

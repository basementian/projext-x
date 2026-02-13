"""Queue API — SmartQueue management endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.api.dependencies import get_config, get_db, get_ebay
from flipflow.core.config import FlipFlowConfig
from flipflow.core.services.lifecycle.smart_queue import SmartQueue

router = APIRouter()


class EnqueueRequest(BaseModel):
    listing_id: int
    priority: int = 0
    window: str = "sunday_surge"


@router.get("/queue/status")
async def queue_status(
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    queue = SmartQueue(ebay, config)
    return await queue.get_queue_status(db)


@router.post("/queue", status_code=201)
async def enqueue(
    data: EnqueueRequest,
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    queue = SmartQueue(ebay, config)
    entry = await queue.enqueue(db, data.listing_id, data.priority, data.window)
    return {"id": entry.id, "listing_id": entry.listing_id, "status": entry.status}


@router.post("/queue/release")
async def release_batch(
    dry_run: bool = False,
    db: AsyncSession = Depends(get_db),
    config: FlipFlowConfig = Depends(get_config),
    ebay=Depends(get_ebay),
):
    queue = SmartQueue(ebay, config)
    released = await queue.release_batch(db, dry_run=dry_run)
    return {
        "released": len(released),
        "dry_run": dry_run,
        "surge_window_active": queue.is_surge_window_active(),
    }

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks

from popframe.models.region import Region
from typing import Any, Dict
from app.utils.get_model import process_models, create_models
from app.utils.data_loader import get_available_regions
from loguru import logger

# Создаем роутер для работы с моделями региона
region_router = APIRouter(prefix="/region", tags=["Region Model"])

# Фоновая задача для пересчета модели региона
async def process_region_model(region_id: int):
    try:
        # Вызываем асинхронную функцию пересчета модели
        await process_models(region_id)
        logger.info(f"Model for region ID {region_id} recalculated successfully.")
    except Exception as e:
        logger.error(f"Error during model recalculation for region ID {region_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model recalculation failed for region ID {region_id}")

# Эндпоинт для пересчета модели региона
@region_router.post("/recalculate_model", response_model=Dict[str, Any])
def recalculate_model_endpoint(
    background_tasks: BackgroundTasks, 
    region_id: int = Query(1, description="Region ID")
):
    background_tasks.add_task(process_region_model, region_id)

    # Немедленный ответ клиенту
    return {"message": "Region model recalculation started", "status": "processing"}

# Endpoint to get available regions
@region_router.get('/get_available_regions', tags=["Region Model"])
def get_regions_endpoin() -> Dict[int, str]:
    return get_available_regions()

@region_router.post('/create_regional_models', tags=["Region Model"])
async def get_models():
    await create_models() 
    return {"message": "Regional models created successfully"}

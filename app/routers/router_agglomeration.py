from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from app.utils.data_loader import get_region
import json
from popframe.method.aglomeration import AgglomerationBuilder
from popframe.models.region import Region
from typing import Any, Dict
import asyncio


agglomeration_router = APIRouter(prefix="/agglomeration", tags=["Agglomeration"])

# Dependency to get the region model
def get_region_model(region_id: int = Query(1, description="Region ID")):
    region_model = get_region(region_id)
    if not isinstance(region_model, Region):
        raise HTTPException(status_code=400, detail="Invalid region model")
    return region_model

# Background task for processing agglomeration
async def process_agglomeration(region_model: Region):
    try:
        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations()
        # Выполнение фоновых действий, например, сохранение результатов в БД или файл
        result = json.loads(agglomeration_gdf.to_json())
        # Здесь можно добавить сохранение в файл или базу данных
        print("Agglomeration processing completed successfully.")
    except Exception as e:
        # Обработка исключений
        print(f"Error during agglomeration processing: {str(e)}")

# Agglomeration Endpoint
@agglomeration_router.get("/build_agglomeration", response_model=Dict[str, Any])
def agglomeration_endpoint(background_tasks: BackgroundTasks, region_model: Region = Depends(get_region_model)):
    background_tasks.add_task(process_agglomeration, region_model)

    # Немедленный ответ клиенту
    return {"message": "Agglomeration building started", "status": "processing"}



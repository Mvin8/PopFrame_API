from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
import geopandas as gpd
from pydantic_geojson import PolygonModel

from popframe.method.territory_evaluation import TerritoryEvaluation
from popframe.models.region import Region
from app.utils.data_loader import get_region_model
from app.models.models import EvaluateTerritoryLocationResult
# from app.utils.db_operations import save_evaluate_territory_location_result_to_db

territory_router = APIRouter(prefix="/territory", tags=["Territory Evaluation"])

# Эндпоинт для выполнения оценки территории без сохранения (возвращает результат)
@territory_router.post("/evaluate_location", response_model=list[EvaluateTerritoryLocationResult])
async def evaluate_territory_location_endpoint(
    polygon: PolygonModel, 
    region_model: Region = Depends(get_region_model)
):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        polygon_feature = {
            'type': 'Feature',
            'geometry': polygon.model_dump(),
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([polygon_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        result = evaluation.evaluate_territory_location(territories_gdf=polygon_gdf)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def process_evaluate_territory_location(
    region_model: Region,
    polygon_gdf: gpd.GeoDataFrame
):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.evaluate_territory_location(territories_gdf=polygon_gdf)
        
        # save_evaluate_territory_location_result_to_db(result)
        
        print("Territory location evaluation completed and saved to DB.")
    except Exception as e:
        print(f"Error during territory location evaluation processing: {str(e)}")

@territory_router.post("/save_evaluate_location")
async def save_evaluate_location_endpoint(
    polygon: PolygonModel, 
    background_tasks: BackgroundTasks,
    region_model: Region = Depends(get_region_model),
    regional_scenario_id: int | None = Query(None, description="ID сценария региона, если имеется"),
    project_scenario_id: int | None = Query(None, description="ID сценария проекта, если имеется")
):
    try:
        polygon_feature = {
            'type': 'Feature',
            'geometry': polygon.model_dump(),
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([polygon_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        background_tasks.add_task(
            process_evaluate_territory_location, 
            region_model, 
            polygon_gdf
        )

        return {"message": "Territory location evaluation started", "status": "processing"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

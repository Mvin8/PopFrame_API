from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks, Request
import requests
import geopandas as gpd
from datetime import datetime
from pydantic_geojson import PolygonModel
from loguru import logger
import sys
from popframe.method.territory_evaluation import TerritoryEvaluation
from popframe.models.region import Region
from app.utils.data_loader import get_region_model
from app.models.models import PopulationCriterionResult

population_router = APIRouter(prefix="/population", tags=["Population Criterion"])

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:MM-DD HH:mm}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
    colorize=True
)


BASE_URL = "'http://10.32.1.107:5300'/api/v1"

# Population Criterion Endpoints
@population_router.post("/test_population_criterion", response_model=list[PopulationCriterionResult])
async def test_population_criterion_endpoint(polygon: PolygonModel, region_model: Region = Depends(get_region_model)):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        polygon_feature = {
            'type': 'Feature',
            'geometry': polygon.model_dump(),
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([polygon_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        result = evaluation.population_criterion(territories_gdf=polygon_gdf)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@population_router.post("/get_population_criterion_score", response_model=list[float])
async def get_population_criterion_score_endpoint(
    geojson_data: dict,
    region_model: Region = Depends(get_region_model),
    regional_scenario_id: int | None = Query(None, description="ID сценария региона, если имеется")
):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        
        if geojson_data.get("type") != "FeatureCollection":
            raise HTTPException(status_code=400, detail="Неверный формат GeoJSON, ожидался FeatureCollection")
        
        polygon_gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        
        scores = []
        result = evaluation.population_criterion(territories_gdf=polygon_gdf)
         
        if result:
            for res in result:
                scores.append(float(res['score']))
            return scores
        
        raise HTTPException(status_code=404, detail="Результаты не найдены")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def process_population_criterion(
    region_model: Region,
    project_scenario_id: int,
    token: str
):
    try:
        scenario_response = requests.get(
            f"{BASE_URL}/scenarios/{project_scenario_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if scenario_response.status_code != 200:
            raise Exception("Ошибка при получении информации по сценарию")
        
        scenario_data = scenario_response.json()
        project_id = int(scenario_data.get("project_id"))
        
        territory_response = requests.get(
            f"{BASE_URL}/projects/{project_id}/territory_info",
            headers={"Authorization": f"Bearer {token}"}
        )
        if territory_response.status_code != 200:
            raise Exception("Ошибка при получении геометрии территории")
        
        territory_data = territory_response.json()
        territory_geometry = territory_data["geometry"]
        territory_feature = {
            'type': 'Feature',
            'geometry': territory_geometry,
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([territory_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)

        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.population_criterion(territories_gdf=polygon_gdf)

        for res in result:
            indicator_data = {
                "scenario_id": project_scenario_id,
                "indicator_id": 197,
                "date_type": "year",
                "date_value": datetime.now().strftime("%Y-%m-%d"),
                "value": float(res['score']),
                "value_type": "real",
                "information_source": "modeled"
            }

            indicators_response = requests.post(
                f"{BASE_URL}/scenarios/{project_scenario_id}/indicators_values",
                headers={"Authorization": f"Bearer {token}"},
                json=indicator_data
            )
            if indicators_response.status_code not in (200, 201):
                logger.error(f"Ошибка при сохранении показателей: {indicators_response.status_code}, "
                             f"Тело ответа: {indicators_response.text}")
                raise Exception("Ошибка при сохранении показателей")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке критерия по населению: {e}")

@population_router.post("/save_population_criterion")
async def save_population_criterion_endpoint(
    background_tasks: BackgroundTasks,
    request: Request,
    region_model: Region = Depends(get_region_model),
    project_scenario_id: int | None = Query(None, description="ID сценария проекта, если имеется")
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token is missing or invalid")
    
    token = auth_header.split(" ")[1]
    background_tasks.add_task(process_population_criterion, region_model, project_scenario_id, token)
    
    return {"message": "Population criterion processing started", "status": "processing"}
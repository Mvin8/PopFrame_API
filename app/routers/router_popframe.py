from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Header,  Request
import geopandas as gpd
from pydantic_geojson import PolygonModel
import requests
import os
from datetime import datetime
from popframe.method.territory_evaluation import TerritoryEvaluation

from popframe.models.region import Region
from app.utils.data_loader import get_region_model
from app.models.models import EvaluateTerritoryLocationResult
from loguru import logger
import sys
import json
from app.utils.auth import verify_token 
from app.utils.config import DEFAULT_CRS, URBAN_API

popframe_router = APIRouter(prefix="/PopFrame", tags=["PopFrame Evaluation"])

logger.remove() 
logger.add(
    sys.stdout,
    format="<green>{time:MM-DD HH:mm}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
    colorize=True
)


async def process_combined_evaluation(
    region_model: Region,
    project_scenario_id: int,
    token: str
):
    try:
        # Общая часть — получение project_id и геометрии территории
        scenario_response = requests.get(
            f"{URBAN_API}/scenarios/{project_scenario_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if scenario_response.status_code != 200:
            raise Exception("Ошибка при получении информации по сценарию")
        
        scenario_data = scenario_response.json()
        project_id = scenario_data.get("project", {}).get("project_id")
        if project_id is None:
            raise Exception("Project ID is missing in scenario data.")
        
        territory_response = requests.get(
            f"{URBAN_API}/projects/{project_id}/territory",
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
        polygon_gdf = gpd.GeoDataFrame.from_features([territory_feature], crs=DEFAULT_CRS)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)

        # Оценка территории
        evaluation = TerritoryEvaluation(region=region_model)

        # Выполнение первой оценки
        location_results = evaluation.evaluate_territory_location(territories_gdf=polygon_gdf)
        for res in location_results:
            closest_settlements = [res["closest_settlement"], res["closest_settlement1"], res["closest_settlement2"]]
            settlements = [settlement for settlement in closest_settlements if settlement]
            interpretation = f'{res["interpretation"]}'
            if settlements:
                interpretation += f' (Ближайший населенный пункт: {", ".join(settlements)}).'

            indicator_data = {
                "indicator_id": 195,
                "scenario_id": project_scenario_id,
                "territory_id": None,
                "hexagon_id": None,
                "value": float(res['score']),
                "comment": interpretation,
                "information_source": "modeled PopFrame",
                "properties": {
                "attribute_name": "Оценка по каркасу расселения"
            }
            }

            indicators_response = requests.put(
                f"{URBAN_API}/scenarios/indicators_values",
                headers={"Authorization": f"Bearer {token}"},
                json=indicator_data
            )
            if indicators_response.status_code not in (200, 201):
                logger.error(f"Ошибка при сохранении показателей (локация): {indicators_response.status_code}, "
                             f"Тело ответа: {indicators_response.text}")
                raise Exception("Ошибка при сохранении показателей (локация)")

        # Выполнение второй оценки
        population_results = evaluation.population_criterion(territories_gdf=polygon_gdf)
        for res in population_results:
            indicator_data = {
                "indicator_id": 197,
                "scenario_id": project_scenario_id,
                "territory_id": None,
                "hexagon_id": None,
                "value": float(res['score']),
                "comment": res['interpretation'],
                "information_source": "modeled PopFrame",
                "properties": {
                "attribute_name": "Население"
            }
            }

            indicators_response = requests.put(
                f"{URBAN_API}/scenarios/indicators_values",
                headers={"Authorization": f"Bearer {token}"},
                json=indicator_data
            )
            if indicators_response.status_code not in (200, 201):
                logger.error(f"Ошибка при сохранении показателей (население): {indicators_response.status_code}, "
                             f"Тело ответа: {indicators_response.text}")
                raise Exception("Ошибка при сохранении показателей (население)")

    except Exception as e:
        logger.error(f"Ошибка при комбинированной обработке: {e}")

@popframe_router.put("/save_popframe_evaluation")
async def save_popframe_evaluation_endpoint(
    background_tasks: BackgroundTasks,
    region_model: Region = Depends(get_region_model),
    project_scenario_id: int | None = Query(None, description="ID сценария проекта, если имеется"),
    token: str = Depends(verify_token)
):
    # Добавляем фоновую задачу для комбинированной обработки
    background_tasks.add_task(process_combined_evaluation, region_model, project_scenario_id, token)
    
    return {"message": "PopFrame evaluation processing started", "status": "processing"}

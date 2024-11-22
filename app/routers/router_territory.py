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

territory_router = APIRouter(prefix="/territory", tags=["Territory Evaluation"])

logger.remove() 
logger.add(
    sys.stdout,
    format="<green>{time:MM-DD HH:mm}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
    colorize=True
)

@territory_router.post("/evaluate_location_test", response_model=list[EvaluateTerritoryLocationResult])
async def evaluate_territory_location_endpoint(
    polygon: PolygonModel, 
    region_model: Region = Depends(get_region_model),
    project_scenario_id: int | None = Query(None, description="ID сценария проекта, если имеется"),
    token: str = Depends(verify_token)  # Добавляем токен для аутентификации
):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        polygon_feature = {
            'type': 'Feature',
            'geometry': polygon.model_dump(),
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([polygon_feature], crs=DEFAULT_CRS)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        result = evaluation.evaluate_territory_location(territories_gdf=polygon_gdf)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def process_evaluation(
    region_model: Region,
    project_scenario_id: int,
    token: str
):
    try:
        # Getting project_id and additional information based on scenario_id
        scenario_response = requests.get(
            f"{URBAN_API}/scenarios/{project_scenario_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if scenario_response.status_code != 200:
            raise Exception("Error retrieving scenario information")
        
        scenario_data = scenario_response.json()
        project_id = scenario_data.get("project", {}).get("project_id")
        if project_id is None:
            raise Exception("Project ID is missing in scenario data.")
        
        # Retrieving territory geometry
        territory_response = requests.get(
            f"{URBAN_API}/projects/{project_id}/territory",
            headers={"Authorization": f"Bearer {token}"}
        )
        if territory_response.status_code != 200:
            raise Exception("Error retrieving territory geometry")
        
        # Extracting only the polygon geometry
        territory_data = territory_response.json()
        territory_geometry = territory_data["geometry"]

        # Converting the territory geometry to GeoDataFrame
        territory_feature = {
            'type': 'Feature',
            'geometry': territory_geometry,
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([territory_feature], crs=DEFAULT_CRS)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
 
        # Territory evaluation
        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.evaluate_territory_location(territories_gdf=polygon_gdf)
        
        # Saving the evaluation to the database
        for res in result:
            closest_settlements = [res["closest_settlement"], res["closest_settlement1"], res["closest_settlement2"]]
            settlements = [settlement for settlement in closest_settlements if settlement]

            # Создаем строку интерпретации
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
                "information_source": "modeled PopFrame"
            }

            indicators_response = requests.post(
                f"{URBAN_API}/scenarios/indicators_values",
                headers={"Authorization": f"Bearer {token}"},
                json=indicator_data
            )
            if indicators_response.status_code not in (200, 201):
                logger.error(f"Error saving indicators: {indicators_response.status_code}, "
                             f"Response body: {indicators_response.text}")
                raise Exception("Error saving indicators")
    except Exception as e:
        logger.error(f"Error in the evaluation process: {e}")


@territory_router.post("/save_evaluate_location")
async def save_evaluate_location_endpoint(
    background_tasks: BackgroundTasks,
    region_model: Region = Depends(get_region_model),
    project_scenario_id: int | None = Query(None, description="Project scenario ID, if available"),
    token: str = Depends(verify_token)  # Добавляем токен для аутентификации
    ):
    # Добавляем фоновую задачу
    background_tasks.add_task(process_evaluation, region_model, project_scenario_id, token)
    
    return {"message": "Population criterion processing started", "status": "processing"}

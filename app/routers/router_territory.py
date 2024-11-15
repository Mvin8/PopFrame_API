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

BASE_URL = os.environ['URBAN_API'] if 'URBAN_API' in os.environ else 'http://10.32.1.107:5300/api/v1'

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
    project_scenario_id: int | None = Query(None, description="ID сценария проекта, если имеется")
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


async def process_evaluation(
    region_model: Region,
    project_scenario_id: int,
    token: str
):
    try:
        # Getting project_id and additional information based on scenario_id
        scenario_response = requests.get(
            f"{BASE_URL}/scenarios/{project_scenario_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if scenario_response.status_code != 200:
            raise Exception("Error retrieving scenario information")
        
        scenario_data = scenario_response.json()
        project_id = int(scenario_data.get("project_id"))  # Convert to standard int
        
        # Retrieving territory geometry
        territory_response = requests.get(
            f"{BASE_URL}/projects/{project_id}/territory",
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
        # with open('poly.json', 'w') as f:
        #     json.dump(territory_feature, f)

        polygon_gdf = gpd.GeoDataFrame.from_features([territory_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
 
        # Territory evaluation
        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.evaluate_territory_location(territories_gdf=polygon_gdf)

        # Saving the evaluation to the database
        for res in result:
            indicator_data = {
                "scenario_id": project_scenario_id,  # Add scenario_id
                "indicator_id": 195,
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
            if indicators_response.status_code not in (200, 201):  # Successful codes: 200 and 201
                logger.error(f"Error saving indicators: {indicators_response.status_code}, "
                             f"Response body: {indicators_response.text}")
                raise Exception("Error saving indicators")
    except Exception as e:
        # Log the error
        logger.error(f"Error in the evaluation process: {e}")

@territory_router.post("/save_evaluate_location")
async def save_evaluate_location_endpoint(
    background_tasks: BackgroundTasks,
    request: Request,
    region_model: Region = Depends(get_region_model),
    project_scenario_id: int | None = Query(None, description="Project scenario ID, if available"),
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token is missing or invalid")
    
    token = auth_header.split(" ")[1]
    # Add a background task that will be executed after the response is returned
    background_tasks.add_task(process_evaluation, region_model, project_scenario_id, token)
    
    # Instantly return a message indicating that processing has started
    return {"message": "Population criterion processing started", "status": "processing"}





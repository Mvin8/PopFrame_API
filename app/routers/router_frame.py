from fastapi import APIRouter, HTTPException, Depends, Query
import json
from popframe.method.popuation_frame import PopulationFrame
from popframe.method.aglomeration import AgglomerationBuilder
from popframe.models.region import Region
from app.utils.data_loader import get_region_model
from typing import Any, Dict

network_router = APIRouter(prefix="/population", tags=["Population Frame"])


@network_router.get("/build_city_frame", response_model=Dict[str, Any])
async def build_circle_frame_endpoint(region_model: Region = Depends(get_region_model)):
    try:
        frame_method = PopulationFrame(region=region_model)
        gdf_frame = frame_method.build_circle_frame()
        return json.loads(gdf_frame.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")


@network_router.get("/build_agglomeration_frames", response_model=Dict[str, Any])
def build_agglomeration_frames(region_model: Region = Depends(get_region_model), regional_scenario_id: int | None = Query(None, description="ID сценария региона, если имеется")):
    try:
        frame_method = PopulationFrame(region=region_model)
        gdf_frame = frame_method.build_circle_frame()

        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations()
        towns_with_status = builder.evaluate_city_agglomeration_status(gdf_frame, agglomeration_gdf)

        agglomeration_gdf['geometry'] = agglomeration_gdf['geometry'].simplify(30, preserve_topology=True)
        towns_with_status['geometry'] = towns_with_status['geometry'].simplify(10, preserve_topology=True)

        agglomerations = json.loads(agglomeration_gdf.to_json())
        towns = json.loads(towns_with_status.to_json())

        result = {
            'agglomerations': agglomerations,
            'towns': towns
        }

        with open("agglomerations_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during city evaluation processing: {str(e)}")

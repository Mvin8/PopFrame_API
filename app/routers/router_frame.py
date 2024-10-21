from fastapi import APIRouter, HTTPException, Depends, Query
import json
from popframe.method.popuation_frame import PopulationFrame
from popframe.models.region import Region
from app.utils.data_loader import get_region_model
from typing import Any, Dict

network_router = APIRouter(prefix="/network", tags=["Network Frame"])

# Network Frame Endpoints
@network_router.get("/build_network_frame", response_model=Dict[str, Any])
async def build_network_endpoint(region_model: Region = Depends(get_region_model)):
    try:
        frame_method = PopulationFrame(region=region_model)
        G = frame_method.build_network_frame()
        gdf_frame = frame_method.save_graph_to_geojson(G, None)
        return json.loads(gdf_frame.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")

@network_router.get("/build_circle_frame", response_model=Dict[str, Any])
async def build_circle_frame_endpoint(region_model: Region = Depends(get_region_model)):
    try:
        frame_method = PopulationFrame(region=region_model)
        gdf_frame = frame_method.build_circle_frame(output_type='gdf')
        return json.loads(gdf_frame.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")

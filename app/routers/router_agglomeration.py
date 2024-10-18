from fastapi import APIRouter, HTTPException, Depends, Query
from app.utils.data_loader import get_region
import json
from popframe.method.aglomeration import AgglomerationBuilder
from popframe.models.region import Region
from typing import Any, Dict

agglomeration_router = APIRouter(prefix="/agglomeration", tags=["Agglomeration"])

# Dependency to get the region model
def get_region_model(region_id: int = Query(1, description="Region ID")):
    region_model = get_region(region_id)
    if not isinstance(region_model, Region):
        raise HTTPException(status_code=400, detail="Invalid region model")
    return region_model

# Agglomeration Endpoint
@agglomeration_router.get("/build_agglomeration", response_model=Dict[str, Any])
def agglomeration_endpoint(region_model: Region = Depends(get_region_model)):
    try:
        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations()
        result = json.loads(agglomeration_gdf.to_json())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during agglomeration processing: {str(e)}")





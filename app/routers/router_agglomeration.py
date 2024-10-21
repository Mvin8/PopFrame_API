from fastapi import APIRouter, HTTPException, Depends, Query
from app.utils.data_loader import get_region_model
import json
from popframe.method.aglomeration import AgglomerationBuilder
from popframe.models.region import Region
from typing import Any, Dict

agglomeration_router = APIRouter(prefix="/agglomeration", tags=["Agglomeration"])

@agglomeration_router.get("/build_agglomeration", response_model=Dict[str, Any])
def get_agglomeration_endpoint(region_model: Region = Depends(get_region_model)):
    try:
        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations()
        result = json.loads(agglomeration_gdf.to_json())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during agglomeration processing: {str(e)}")





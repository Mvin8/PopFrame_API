from fastapi import APIRouter, HTTPException, Depends
import json
import geopandas as gpd
from pydantic_geojson import PolygonModel
from typing import Any, Dict
from popframe.method.landuse_assessment import LandUseAssessment
from popframe.models.region import Region
from app.utils.data_loader import get_region_model

landuse_router = APIRouter(prefix="/landuse", tags=["Landuse data"])


# Land Use Data Endpoints
@landuse_router.post("/get_landuse_data", response_model=Dict[str, Any])
async def get_landuse_data_endpoint(polygon : PolygonModel, region_model: Region = Depends(get_region_model)):
    try:
        urbanisation = LandUseAssessment(region=region_model)
        polygon_feature = {
        'type': 'Feature',
        'geometry' : polygon.model_dump(),
        'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([polygon_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        landuse_data = urbanisation.get_landuse_data(territories=polygon_gdf)
        return json.loads(landuse_data.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


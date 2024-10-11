from fastapi import APIRouter, HTTPException, Depends, Query
import geopandas as gpd
from pydantic_geojson import PolygonModel

from popframe.method.territory_evaluation import TerritoryEvaluation
from popframe.models.region import Region
from app.utils.data_loader import get_region
from app.models.models import PopulationCriterionResult

population_router = APIRouter(prefix="/population", tags=["Population Criteria"])

# Dependency to get the region model
def get_region_model(region_id: int = Query(1, description="Region ID")):
    region_model = get_region(region_id)
    if not isinstance(region_model, Region):
        raise HTTPException(status_code=400, detail="Invalid region model")
    return region_model


# Population Criterion Endpoints
@population_router.post("/population_criterion", response_model=list[PopulationCriterionResult])
async def population_criterion_endpoint(polygon: PolygonModel, region_model: Region = Depends(get_region_model)):
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

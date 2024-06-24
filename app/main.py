from fastapi import FastAPI, HTTPException, APIRouter, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List, Optional
import json
import geopandas as gpd

from popframe.method.territory_evaluation import TerritoryEvaluation
from popframe.method.urbanisation_level import UrbanisationLevel
from popframe.models.region import Region
from popframe.method.popuation_frame import PopFrame

from app.models.models import (
    GeoJSONRequest, CriteriaRequest, EvaluateTerritoryLocationResult,
    PopulationCriterionResult, CalculatePotentialResult, BuildNetworkResult
)

from app.utils.data_loader import get_region, load_geodata, get_available_regions

app = FastAPI(
    title="PopFrame API",
    description="API for PopFrame service, handling territory evaluation, population criteria, network frame, and land use data.",
    version="1.0.0",
    contact={
        "name": "Maksim Natykin",
        "email": "mvin@itmo.ru",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Список доменов, с которых разрешены запросы. "*" позволяет все домены.
    allow_credentials=True,
    allow_methods=["*"],  # Список разрешенных методов (GET, POST и т.д.). "*" позволяет все методы.
    allow_headers=["*"],  # Список разрешенных заголовков. "*" позволяет все заголовки.
)

# Create routers
territory_router = APIRouter(prefix="/territory", tags=["Territory Evaluation"])
population_router = APIRouter(prefix="/population", tags=["Population Criteria"])
network_router = APIRouter(prefix="/network", tags=["Network Frame"])
landuse_router = APIRouter(prefix="/landuse", tags=["Land Use Data"])

# Dependency to get the region model
def get_region_model(region_id: int = Query(47, description="Region ID")):
    region_model = get_region(region_id)
    if not isinstance(region_model, Region):
        raise HTTPException(status_code=400, detail="Invalid region model")
    return region_model

# Dependency to get geodata
def get_geodata(region_id: int = Query(47, description="Region ID")):
    gdf = load_geodata(region_id)
    return gdf

# Endpoint to get available regions
@app.get('/regions', tags=["Regions"])
def regions() -> Dict[int, str]:
    return get_available_regions()

# Territory Evaluation Endpoints
@territory_router.post("/evaluate_location", response_model=List[EvaluateTerritoryLocationResult])
async def evaluate_territory_location_endpoint(request: GeoJSONRequest, region_model: Region = Depends(get_region_model)):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.evaluate_territory_location(territories=request.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@territory_router.post("/population_criterion", response_model=List[PopulationCriterionResult])
async def population_criterion_endpoint(request: GeoJSONRequest, region_model: Region = Depends(get_region_model), gdf = Depends(get_geodata)):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.population_criterion(gdf, territories=request.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Population Criteria Endpoints
@population_router.post("/calculate_potential", response_model=List[CalculatePotentialResult])
async def calculate_potential_endpoint(request: CriteriaRequest, region_model: Region = Depends(get_region_model)):
    try:
        territories_criteria = {
            "Население": request.population,
            "Транспорт": request.transport,
            "Экология": request.ecology,
            "Соц-об": request.social_objects,
            "Инж инф": request.engineering_infrastructure,
        }

        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.calculate_potential(territories_criteria)
        
        formatted_result = [
            {"category": category, "scores": scores}
            for category, scores in result
        ]
        
        return formatted_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Network Frame Endpoints
@network_router.post("/build_network_frame", response_model=Dict[str, Any])
async def build_network_endpoint(region_model: Region = Depends(get_region_model)):
    try:
        frame_method = PopFrame(region=region_model)
        G = frame_method.build_network_frame()
        gdf_frame = frame_method.save_graph_to_geojson(G, None)
        
        return json.loads(gdf_frame.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")

@network_router.post("/build_square_frame", response_model=Dict[str, Any])
async def build_square_frame_endpoint(region_model: Region = Depends(get_region_model)):
    try:
        frame_method = PopFrame(region=region_model)
        gdf_frame = frame_method.build_square_frame(output_type='gdf')
        return json.loads(gdf_frame.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")

# Land Use Data Endpoints
@landuse_router.post("/get_landuse_data", response_model=Dict[str, Any])
async def get_landuse_data_endpoint(request: GeoJSONRequest, region_model: Region = Depends(get_region_model)):
    try:
        urbanisation = UrbanisationLevel(region=region_model)
        landuse_data = urbanisation.get_landuse_data(territories=request.model_dump())
        return json.loads(landuse_data.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Root endpoint
@app.get("/", response_model=Dict[str, str])
def read_root():
    return {"message": "Welcome to PopFrame Service"}

# Include routers in the main app
app.include_router(territory_router)
app.include_router(population_router)
app.include_router(network_router)
app.include_router(landuse_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
from pydantic_geojson import PolygonModel, MultiPolygonModel
from pydantic import BaseModel, Field

class Request(BaseModel):
    type: str = Field(..., example="Polygon")
    geometry: Union[PolygonModel, MultiPolygonModel]

class CriteriaRequest(BaseModel):
    population: int
    transport: int
    ecology: int
    social_objects: int
    engineering_infrastructure: int

class EvaluateTerritoryLocationResult(BaseModel):
    territory: str
    score: int
    interpretation: str
    closest_settlement: str
    closest_settlement1: Optional[str]
    closest_settlement2: Optional[str]

class PopulationCriterionResult(BaseModel):
    project: Optional[str]
    average_population_density: float
    total_population: float
    score: int

class CalculatePotentialResult(BaseModel):
    category: str
    scores: List[int]

class BuildNetworkResult(BaseModel):
    geojson: Dict[str, Any]
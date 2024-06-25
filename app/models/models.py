from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class GeoJSONRequest(BaseModel):
    type: str
    features: list

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
    average_population_growth: float
    score: int

class CalculatePotentialResult(BaseModel):
    category: str
    scores: List[int]

class BuildNetworkResult(BaseModel):
    geojson: Dict[str, Any]
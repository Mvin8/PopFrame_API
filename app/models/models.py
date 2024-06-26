from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class GeoJSONRequest(BaseModel):
    type: str = Field(..., example="FeatureCollection")
    features: list = Field(
        ...,
        example=[
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "coordinates": [
                        [
                            [29.982879431084967, 59.363554752593245],
                            [29.982879431084967, 59.322083801173534],
                            [30.109075699649765, 59.322083801173534],
                            [30.109075699649765, 59.363554752593245],
                            [29.982879431084967, 59.363554752593245],
                        ]
                    ],
                    "type": "Polygon"
                }
            }
        ]
    )

    
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
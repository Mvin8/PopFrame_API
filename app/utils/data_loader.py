import os
from fastapi import APIRouter, HTTPException, Depends, Query
from app.utils.get_model import check_model_exists
from popframe.models.region import Region
from app.utils.config import DATA_PATH
import os 

def _get_region_data_path(region_id: int):
    if not region_id:
        raise ValueError(f"Region ID {region_id} is not recognized.")
    return os.path.join(DATA_PATH, f'{region_id}.pickle')

def get_region(region_id: int):
    return Region.from_pickle(_get_region_data_path(region_id))

def get_available_regions():
    available_regions = {}
    for file_name in os.listdir(DATA_PATH):
        if file_name.endswith('.pickle'):
            region_id = int(file_name.split('.')[0])
            model_exists, model_file = check_model_exists(region_id)
            if model_exists:
                available_regions[region_id] = f"Region {region_id}" 
    return available_regions

# Dependency to get the region model
def get_region_model(region_id: int = Query(1, description="Region ID")):
    region_model = get_region(region_id)
    if not isinstance(region_model, Region):
        raise HTTPException(status_code=400, detail="Invalid region model")
    return region_model
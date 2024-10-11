import os
import requests
import pandas as pd
import geopandas as gpd
import numpy as np
import pickle

from shapely.geometry import Point
from app.utils.data_loader import REGIONS_DICT, DATA_PATH, REGIONS_CRS

from popframe.preprocessing.level_filler import LevelFiller
from popframe.models.region import Region
from idu_clients import UrbanAPI

async def load_region_bounds(region_id: int) -> gpd.GeoDataFrame:
    urban_api = UrbanAPI('http://10.32.1.107:5300')
    regions = await urban_api.get_regions()
    if regions.empty:
        region_name = REGIONS_DICT.get(region_id, f"Region ID {region_id}")
        raise FileNotFoundError(f"Region bounds for {region_name} not found.")
    region = regions.loc[[region_id]]
    return region

async def load_accessibility_matrix(region_id : int, graph_type : str) -> pd.DataFrame:
    res = requests.get('http://10.32.1.65:5700' + f'/api_v1/{region_id}/get_matrix', {
        'graph_type': graph_type
    })
    json = res.json()
    adj_mx = pd.DataFrame(json['values'], index=json['index'], columns=json['columns'])
    if adj_mx.empty:
        region_name = REGIONS_DICT.get(region_id, f"Region ID {region_id}")
        raise FileNotFoundError(f"Matrix for {region_name} not found.")
    return adj_mx

async def get_region_territories(region_id : int) -> dict[int, gpd.GeoDataFrame]:
    res = requests.get('http://10.32.1.107:5300' + '/api/v1/all_territories', {
        'parent_id': region_id,
        'get_all_levels': True
    })
    gdf = gpd.GeoDataFrame.from_features(res.json()['features'], crs=4326)
    df = pd.json_normalize(gdf['territory_type']).rename(columns={
        'name':'territory_type_name'
    })
    gdf = pd.DataFrame.join(gdf, df).set_index('territory_id', drop=True)
    return {level:gdf[gdf['level'] == level] for level in set(gdf.level)}

async def load_towns(region_id: int) -> gpd.GeoDataFrame:
    gdfs_dict = await get_region_territories(region_id)
    if not gdfs_dict:
        region_name = REGIONS_DICT.get(region_id, f"Region ID {region_id}")
        raise FileNotFoundError(f"Towns for {region_name} not found.")
    
    last_key, last_value = list(gdfs_dict.items())[-1]
    last_value['geometry'] = last_value['geometry'].representative_point()  
    last_value['population'] = np.random.randint(100, 3000000, size=len(last_value))
    level_filler = LevelFiller(towns=last_value)
    towns = level_filler.fill_levels()
    return towns

async def get_model(region, towns, adj_mx, region_id, local_crs):
    try:
        region_model = Region(
            region = region.to_crs(local_crs),
            towns=towns.to_crs(local_crs),
            accessibility_matrix=adj_mx
            )
        return region_model
    except Exception as e:
        region_name = REGIONS_DICT.get(region_id, f"Region ID {region_id}")
        raise RuntimeError(f"Error calculating the matrix for region {region_name}: {str(e)}")
    
def check_model_exists(region_id: int):
    region_name = REGIONS_DICT.get(region_id)
    model_file = os.path.join(DATA_PATH,  f'{region_name}.pickle')
    return os.path.exists(model_file), model_file

def to_pickle(data, file_path: str) -> None:
    with open(file_path, "wb") as f:
        pickle.dump(data, f)

async def process_models():
    for region_id, region_name in REGIONS_DICT.items():
        print(f"Load model for {region_name}...")
        model_exists, model_file = check_model_exists(region_id)
        if model_exists:
            print(f"Model for {region_name} already exists")
            continue 
        print(f"Model for {region_name} not found. Creating...")
        local_crs = REGIONS_CRS[region_id]
        try:
            region = await load_region_bounds(region_id)
        except FileNotFoundError as e:
            print(f"Error loading region bounds for {region_name}: {e}")
            continue
        try:
            towns = await load_towns(region_id)
        except FileNotFoundError as e:
            print(f"Error loading towns for {region_name}: {e}")
            continue
        try:
            adj_mx = await load_accessibility_matrix(region_id, 'drive')
        except FileNotFoundError as e:
            print(f"Error loading accessibility matrix for {region_name}: {e}")
            continue
        try:
            model = await get_model(region, towns, adj_mx, region_id, local_crs)
            to_pickle(model, model_file)
        except RuntimeError as e:
            print(f"Error creating model for {region_name}: {e}")
            continue
        print(f'Model for {region_name} has been successfully created')
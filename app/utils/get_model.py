import os
import requests
import pandas as pd
import geopandas as gpd
import numpy as np
import pickle
from loguru import logger

from app.utils.config import DATA_PATH

from popframe.preprocessing.level_filler import LevelFiller
from popframe.models.region import Region
from idu_clients import UrbanAPI

async def load_region_bounds(region_id: int) -> gpd.GeoDataFrame:
    urban_api = UrbanAPI('http://10.32.1.107:5300')
    regions = await urban_api.get_regions()
    if regions.empty:
        raise FileNotFoundError(f"Region bounds for {region_id} not found.")
    region = regions.loc[[region_id]]
    return region

async def load_accessibility_matrix(region_id : int, graph_type : str) -> pd.DataFrame:
    res = requests.get('http://10.32.1.65:5700' + f'/api_v1/{region_id}/get_matrix', {
        'graph_type': graph_type
    })
    json = res.json()
    adj_mx = pd.DataFrame(json['values'], index=json['index'], columns=json['columns'])
    if adj_mx.empty:
        raise FileNotFoundError(f"Matrix for {region_id} not found.")
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
        raise FileNotFoundError(f"Towns for {region_id} not found.")
    
    last_key, last_value = list(gdfs_dict.items())[-1]
    last_value['geometry'] = last_value['geometry'].representative_point()  
    last_value['population'] = np.random.randint(100, 3000000, size=len(last_value))
    last_value['id'] = last_value.index
    level_filler = LevelFiller(towns=last_value)
    towns = level_filler.fill_levels()
    return towns

def check_model_exists(region_id: int):
    model_file = os.path.join(DATA_PATH, f'{region_id}.pickle')
    return os.path.exists(model_file), model_file

async def get_model(region, towns, adj_mx, region_id, local_crs):
    try:
        region_model = Region(
            region = region.to_crs(local_crs),
            towns=towns.to_crs(local_crs),
            accessibility_matrix=adj_mx
            )
        return region_model
    except Exception as e:
        raise RuntimeError(f"Error calculating the matrix for region {region_id}: {str(e)}")
    
def to_pickle(data, file_path: str) -> None:
    with open(file_path, "wb") as f:
        pickle.dump(data, f)

async def create_models(region_id: int = None):

    try:
        regions = await load_region_bounds(region_id) if region_id is not None else await load_region_bounds()
        logger.info("Regions bounds loaded")
    except FileNotFoundError as e:
        logger.error("Error loading regions bounds")
        return
    
    if region_id is not None:
        regions = regions.loc[[region_id]] 

    for region_id, region in regions.iterrows():
        region = regions.loc[[region_id]]
        local_crs = region.geometry.estimate_utm_crs()
        logger.info(f"Creating model for {region_id}...")

        try:
            towns = await load_towns(region_id)
            logger.info(f"Towns loaded for {region_id}")
        except FileNotFoundError as e:
            logger.error(f"Error loading towns for {region_id}: {e}")
            return

        try:
            adj_mx = await load_accessibility_matrix(region_id, 'drive')
            logger.info(f"Accessibility matrix loaded for {region_id}")
        except FileNotFoundError as e:
            logger.error(f"Error loading accessibility matrix for {region_id}: {e}")
            return

        try:
            model = await get_model(region, towns, adj_mx, region_id, local_crs)
            model_file = os.path.join(DATA_PATH, f'{region_id}.pickle')
            to_pickle(model, model_file)
            logger.info(f"Model for {region_id} successfully created and saved.")
        except RuntimeError as e:
            logger.error(f"Error creating model for {region_id}: {e}")
            return

async def process_models(region_id: int = None):
    # Если передан region_id, то обрабатываем только его
    if region_id is not None:
        logger.info(f"Processing model for region ID {region_id}...")
        model_exists, model_file = check_model_exists(region_id)

        # Если модель существует, удаляем её и пересоздаем
        if model_exists:
            logger.info(f"Model for region ID {region_id} already exists. Deleting and recreating...")
            try:
                os.remove(model_file)
                logger.info(f"Old model for region ID {region_id} deleted.")
            except OSError as e:
                logger.error(f"Error deleting model for region ID {region_id}: {e}")
                return

        # Создаем новую модель
        await create_models(region_id)

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

URBAN_API = os.environ['URBAN_API'] if 'URBAN_API' in os.environ else 'http://10.32.1.107:5300/api/v1'
POPULATION_COUNT_INDICATOR_ID = 1
DEFAULT_CRS = 4326

def get_territories_population(territories_gdf : gpd.GeoDataFrame):
    res = requests.get(f'{URBAN_API}/indicator/{POPULATION_COUNT_INDICATOR_ID}/values')
    res_df = pd.DataFrame(res.json())
    res_df = res_df[res_df['territory'].apply(lambda x: x['id'] if isinstance(x, dict) else None).isin(territories_gdf.index)]
    res_df = (
        res_df
        .groupby(res_df['territory'].apply(lambda x: x['id'] if isinstance(x, dict) else None))
        .agg({'value': 'last'})
        .rename(columns={'value': 'population'})
    )
    return territories_gdf[['geometry', 'name']].merge(res_df, left_index=True, right_index=True)

async def get_country_regions(country_id : int) -> pd.DataFrame:
    res = requests.get(f'{URBAN_API}/all_territories', {
        'parent_id':country_id
    })
    return gpd.GeoDataFrame.from_features(res.json()['features'], crs=DEFAULT_CRS).set_index('territory_id', drop=True)

async def get_countries_without_geometry() -> pd.DataFrame:
    res = requests.get(f'{URBAN_API}/all_territories_without_geometry')
    return pd.DataFrame(res.json()).set_index('territory_id', drop=True)

async def get_regions():
    countries = await get_countries_without_geometry()
    countries_ids = countries.index
    countries_regions = [await get_country_regions(country_id) for country_id in countries_ids]
    return pd.concat(countries_regions)

async def load_region_bounds() -> gpd.GeoDataFrame:
    regions = await get_regions()
    return regions

async def load_accessibility_matrix(region_id : int, graph_type : str) -> pd.DataFrame:
    res = requests.get('http://10.32.1.65:5700' + f'/api_v1/{region_id}/get_matrix', {
        'graph_type': graph_type
    })
    json = res.json()
    adj_mx = pd.DataFrame(json['values'], index=json['index'], columns=json['columns'])
    if adj_mx.empty:
        raise FileNotFoundError(f"Matrix for {region_id} not found.")
    return adj_mx

def get_territories(parent_id : int | None = None, all_levels = False, geometry : bool = False) -> pd.DataFrame | gpd.GeoDataFrame:
    res = requests.get(f'{URBAN_API}/all_territories{"" if geometry else "_without_geometry"}', {
        'parent_id': parent_id,
        'get_all_levels': all_levels
    })
    res_json = res.json()
    if geometry:
        gdf = gpd.GeoDataFrame.from_features(res_json, crs=DEFAULT_CRS)
        return gdf.set_index('territory_id', drop=True)
    df = pd.DataFrame(res_json)
    return df.set_index('territory_id', drop=True)

def load_towns(region_id: int) -> gpd.GeoDataFrame:
    territories_gdf = get_territories(region_id, all_levels = True, geometry=True)
    towns_gdf = territories_gdf[territories_gdf['is_city'] == True]
    towns_gdf['geometry'] = towns_gdf['geometry'].representative_point()
    towns_gdf = get_territories_population(towns_gdf)
    towns_gdf['id'] = towns_gdf.index
    level_filler = LevelFiller(towns=towns_gdf)
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
        if region_id is not None:
            regions = await load_region_bounds()
            regions = regions.loc[[region_id]]
            logger.info("Regions bounds loaded")
        else:
            regions = await load_region_bounds()
    except FileNotFoundError as e:
        logger.error("Error loading regions bounds")
        return

    for region_id, region in regions.iterrows():
        region = regions.loc[[region_id]]
        local_crs = region.geometry.estimate_utm_crs()
        logger.info(f"Creating model for {region_id}...")

        try:
            towns = load_towns(region_id)
            logger.info(f"Towns loaded for {region_id}")
        except FileNotFoundError as e:
            logger.error(f"Error loading towns for {region_id}: {e}")
            return

        try:
            adj_mx = await load_accessibility_matrix(region_id, 'car')
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

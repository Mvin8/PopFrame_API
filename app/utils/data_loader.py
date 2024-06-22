import os
import pandas as pd
import geopandas as gpd

from popframe.models.region import Region

REGIONS_DICT = {
    47: 'Ленинградская область',
    78: 'Санкт-Петербург',
    77: 'Москва',
    34: 'Волгоградская область',
    71: 'Тульская область',
    55: 'Омская область',
    23: 'Краснодарский край',
    72: 'Тюменская область',
    50: 'Московская область',
}

DATA_PATH = os.path.abspath('app/data')

def _get_region_data_path(region_id: int):
    region_name = REGIONS_DICT.get(region_id)
    if not region_name:
        raise ValueError(f"Region ID {region_id} is not recognized.")
    return os.path.join(DATA_PATH, f'{region_name}.pickle')

def get_region(region_id: int):
    return Region.from_pickle(_get_region_data_path(region_id))

def load_geodata(region_id: int):
    return gpd.read_parquet(os.path.join(DATA_PATH, 'mo_desteny_growth.parquet'))

def get_available_regions():
    return REGIONS_DICT


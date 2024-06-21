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


def _get_region_data_path(region_id : int):
    return os.path.join(DATA_PATH, str(region_id))

def get_region(region_id : int):
    return Region.from_pickle(os.path.join(_get_region_data_path(region_id), f'{region_id}.pickle'))
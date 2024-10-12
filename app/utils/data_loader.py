import os

from popframe.models.region import Region

REGIONS_DICT = {
    1: 'Ленинградская область',
    3138: 'Санкт-Петербург',
    3268: 'Москва',
    3427: 'Волгоградская область',
    3902: 'Тульская область',
    4013: 'Омская область',
    4437: 'Краснодарский край',
    4882: 'Тюменская область',
    5188: 'Московская область',
    }

REGIONS_CRS = {
    1: 32636,
    3138: 32636,
    3268: 32637,
    3427: 32638,
    3902: 32637,
    4013: 32643,
    4437: 32637,
    4882: 32642,
    5188: 32637,
}

DATA_PATH = os.path.abspath('app/data')

def _get_region_data_path(region_id: int):
    region_name = REGIONS_DICT.get(region_id)
    if not region_name:
        raise ValueError(f"Region ID {region_id} is not recognized.")
    return os.path.join(DATA_PATH, f'{region_name}.pickle')

def get_region(region_id: int):
    return Region.from_pickle(_get_region_data_path(region_id))

def get_available_regions():
    return REGIONS_DICT


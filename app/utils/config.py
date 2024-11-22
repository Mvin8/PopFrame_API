import os

DATA_PATH = os.path.abspath('app/data')

import os

if 'URBAN_API' in os.environ:
    URBAN_API = os.environ['URBAN_API']
else:
    raise Exception('URBAN_API not found in env variables')

if 'TRANSPORT_FRAMES_API' in os.environ:
    TRANSPORT_FRAMES_API = os.environ['TRANSPORT_FRAMES_API']
else:
    raise Exception('TRANSPORT_FRAMES_API not found in env variables')
    
POPULATION_COUNT_INDICATOR_ID = 1
DEFAULT_CRS = 4326
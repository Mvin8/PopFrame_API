import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Пример данных GeoJSON
geojson_data = {
    "type": "FeatureCollection",
    "name": "project Шлиссельбург",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    "features": [
        { "type": "Feature", "properties": { "building": None, "name": "Шлиссельбург", "addr:street": None, "addr:housenumber": None, "addr:city": None, "type": "project", "is_living": None }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 30.993913172856011, 59.924597611350642 ], [ 30.999718075936872, 59.92939124524851 ], [ 31.02331219813648, 59.925349599879553 ], [ 31.051774948726486, 59.922247536976649 ], [ 31.049527889469388, 59.916794721233835 ], [ 31.047655340088465, 59.915572415065995 ], [ 31.044659261078984, 59.908989990082127 ], [ 31.003837684574897, 59.909178077541952 ], [ 31.001216115441608, 59.911058893338229 ], [ 30.992976898165544, 59.910964855087578 ], [ 30.989793564217987, 59.915196311774075 ], [ 30.989793564217987, 59.919239198078628 ], [ 30.993913172856011, 59.924597611350642 ] ] ] } }
    ]
}

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to PopFrame Service"}

def test_get_regions():
    response = client.get("/regions")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_evaluate_territory_location():
    response = client.post("/territory/evaluate_location", json=geojson_data)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_population_criterion():
    response = client.post("/territory/population_criterion", json=geojson_data)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_calculate_potential():
    sample_request = {
        "population": 1000,
        "transport": 500,
        "ecology": 300,
        "social_objects": 200,
        "engineering_infrastructure": 100
    }
    response = client.post("/population/calculate_potential", json=sample_request)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_build_network_frame():
    response = client.post("/network/build_network_frame")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_build_square_frame():
    response = client.post("/network/build_square_frame")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_get_landuse_data():
    response = client.post("/landuse/get_landuse_data", json=geojson_data)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

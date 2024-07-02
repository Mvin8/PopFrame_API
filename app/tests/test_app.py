import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Пример данных GeoJSON
geojson_data = {
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "coordinates": [
          [
            [
              29.982879431084967,
              59.363554752593245
            ],
            [
              29.982879431084967,
              59.322083801173534
            ],
            [
              30.109075699649765,
              59.322083801173534
            ],
            [
              30.109075699649765,
              59.363554752593245
            ],
            [
              29.982879431084967,
              59.363554752593245
            ]
          ]
        ],
        "type": "Polygon"
      }
    }
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
        "population": 1,
        "transport": 5,
        "ecology": 3,
        "social_objects": 2,
        "engineering_infrastructure": 1
    }
    response = client.post("/population/calculate_potential", json=sample_request)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_build_network_frame():
    response = client.get("/network/build_network_frame")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_build_square_frame():
    response = client.get("/network/build_square_frame")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_get_landuse_data():
    response = client.post("/landuse/get_landuse_data", json=geojson_data)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

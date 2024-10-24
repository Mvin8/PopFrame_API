from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
import geopandas as gpd
from pydantic_geojson import PolygonModel

from popframe.method.territory_evaluation import TerritoryEvaluation
from popframe.models.region import Region
from app.utils.data_loader import get_region_model
#from app.utils.db_operations import save_population_criterion_result_to_db
from app.models.models import PopulationCriterionResult
population_router = APIRouter(prefix="/population", tags=["Population Criterion"])



# Population Criterion Endpoints
@population_router.post("/test_population_criterion", response_model=list[PopulationCriterionResult])
async def test_population_criterion_endpoint(polygon: PolygonModel, region_model: Region = Depends(get_region_model)):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        polygon_feature = {
            'type': 'Feature',
            'geometry': polygon.model_dump(),
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([polygon_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        result = evaluation.population_criterion(territories_gdf=polygon_gdf)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def process_population_criterion(
    region_model: Region,
    polygon_gdf: gpd.GeoDataFrame,
    regional_scenario_id: int | None,
    project_scenario_id: int | None
):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        result = evaluation.population_criterion(territories_gdf=polygon_gdf)
        
        # save_population_criterion_result_to_db(
        #     result=result, 
        #     regional_scenario_id=regional_scenario_id, 
        #     project_scenario_id=project_scenario_id
        # )
        
        print("Population criterion processing completed and saved to DB.")
    except Exception as e:
        print(f"Error during population criterion processing: {str(e)}")


# Population Criterion Endpoint
@population_router.post("/save_population_criterion")
async def save_population_criterion_endpoint(
    polygon: PolygonModel, 
    background_tasks: BackgroundTasks,
    region_model: Region = Depends(get_region_model),
    regional_scenario_id: int | None = Query(None, description="ID сценария региона, если имеется"),
    project_scenario_id: int | None = Query(None, description="ID сценария проекта, если имеется")
):
    try:
        polygon_feature = {
            'type': 'Feature',
            'geometry': polygon.model_dump(),
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([polygon_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)

        background_tasks.add_task(
            process_population_criterion,
            region_model,
            polygon_gdf,
            regional_scenario_id,
            project_scenario_id
        )
        return {"message": "Population criterion processing started", "status": "processing"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@population_router.post("/get_population_criterion_score", response_model=list[float])
async def get_population_criterion_score_endpoint(
    geojson_data: dict,
    region_model: Region = Depends(get_region_model),
    regional_scenario_id: int | None = Query(None, description="ID сценария региона, если имеется")
):
    try:
        evaluation = TerritoryEvaluation(region=region_model)
        
        # Проверяем, что пришел правильный формат данных
        if geojson_data.get("type") != "FeatureCollection":
            raise HTTPException(status_code=400, detail="Неверный формат GeoJSON, ожидался FeatureCollection")
        
        # Создаем GeoDataFrame из features
        polygon_gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(region_model.crs)
        
        # Вызываем метод оценки для каждого полигона
        scores = []
        result = evaluation.population_criterion(territories_gdf=polygon_gdf)
        
        if result:
            for res in result:
                scores.append(float(res['score']))  # Преобразуем значение в float и добавляем в список
            return scores
        
        raise HTTPException(status_code=404, detail="Результаты не найдены")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


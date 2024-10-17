from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import router_territory
from app.routers import router_population
from app.routers import router_frame
from app.routers import router_agglomeration
from app.utils.data_loader import get_available_regions
from app.utils import get_model
from typing import Dict
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:MM-DD HH:mm}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
    colorize=True
)


app = FastAPI(
    title="PopFrame API",
    description="API for PopFrame service, handling territory evaluation, population criteria, network frame, and land use data.",
    version="1.0.0",
    contact={
        "name": "Maksim Natykin",
        "email": "mvin@itmo.ru",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint to get available regions
@app.get('/regions', tags=["Regions"])
def regions() -> Dict[int, str]:
    return get_available_regions()

# Root endpoint
@app.get("/", response_model=Dict[str, str])
def read_root():
    return {"message": "Welcome to PopFrame Service"}

# Include routers
app.include_router(router_territory.territory_router)
app.include_router(router_population.population_router)
app.include_router(router_frame.network_router)
app.include_router(router_agglomeration.agglomeration_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# @app.on_event("startup")
# async def startup_event():
#     await get_model.process_models()



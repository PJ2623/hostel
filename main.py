from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from routers import user, duties, auth

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

@asynccontextmanager
async def connect_to_mongo(app: FastAPI):
    # * Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    await init_beanie(database=client["greenCloudMVP"], document_models=[])
    yield
    

app = FastAPI(
    title="Hostel Management",
    description="An API for St Joseph's Hostel Management",
    lifespan=connect_to_mongo,
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(duties.router)
app.include_router(auth.router)
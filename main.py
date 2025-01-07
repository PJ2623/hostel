import uvicorn

from pytz import utc

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.helpers import assign_saturday_duties

from contextlib import asynccontextmanager

from routers import duty, staff, auth, learner

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models.duty import AssignedDuties, Duties
from models.learner import Learners
from models.staff import Staff
from utils.models import DefaultDocs


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient("mongodb://localhost:27017")     # * Connect to MongoDB
    
    #* Create a scheduler to assign duties to learners every Saturday at midnight
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(hour=0, minute=53)
    
    scheduler.add_job(assign_saturday_duties, trigger)
    
    await init_beanie(database=client["hostelManagement"], document_models=[Duties, Learners, Staff, DefaultDocs, AssignedDuties])
    scheduler.start()
    yield
    scheduler.shutdown()
    client.close()
    

app = FastAPI(
    title="Hostel Management",
    description="An API for St Joseph's Hostel Management",
    lifespan=lifespan,
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(staff.router)
app.include_router(duty.router)
app.include_router(learner.router)
app.include_router(auth.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from contextlib import asynccontextmanager

from routers import user, duties, auth

from cache import redis


@asynccontextmanager
async def lifespan(_: FastAPI):
    await FastAPILimiter.init(redis)
    yield
    await FastAPILimiter.close()
    

app = FastAPI(
    title="Hostel Management",
    description="An API for St Joseph's Hostel Management",
    lifespan=lifespan,
    debug=True
)

app.include_router(user.router)
app.include_router(duties.router)
app.include_router(auth.router)
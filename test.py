from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/greeting")
async def greeting():
    return JSONResponse(
        status_code=200, content={"message": "Hello", "time": str(datetime.now())}
    )

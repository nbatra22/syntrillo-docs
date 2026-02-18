from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes import blood_pressure

app = FastAPI(
    title="Syntrillo API",
    description="Syntrillo clinical platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    blood_pressure.router,
    prefix="/api/v1/blood-pressure",
    tags=["Blood Pressure"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}
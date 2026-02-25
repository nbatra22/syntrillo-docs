from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routes import blood_pressure, risk_score, devices

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

app.include_router(
    risk_score.router,
    prefix="/api/v1/risk-score",
    tags=["Risk Score"],
)

app.include_router(
    devices.router,
    prefix="/api/v1/devices",
    tags=["Devices"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}
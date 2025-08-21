"""
Main FastAPI application for healthcare scenarios API.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional

from .config import settings
from .db import init_db, close_db
from .repositories import ReferenceRepository
from .services import ScenarioService
from .schemas import (
    ApiResponse, PaginatedResponse, ScenarioRequest, ScenarioResponse,
    ErrorResponse
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Extended API for healthcare scenario planning with FTE and seasonality support",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ref_repo = ReferenceRepository()
scenario_service = ScenarioService()


# Reference endpoints
@app.get("/reference/sites", response_model=ApiResponse)
async def get_sites():
    """Get all hospital sites."""
    try:
        sites = await ref_repo.get_sites()
        return ApiResponse(
            data=sites,
            meta={"count": len(sites)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reference/programs", response_model=ApiResponse)
async def get_programs():
    """Get all healthcare programs."""
    try:
        programs = await ref_repo.get_programs()
        return ApiResponse(
            data=programs,
            meta={"count": len(programs)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reference/staffed-beds", response_model=ApiResponse)
async def get_staffed_beds(
    schedule: str = Query("Sched-A", description="Schedule code")
):
    """Get staffed beds by schedule."""
    try:
        beds = await ref_repo.get_staffed_beds(schedule)
        return ApiResponse(
            data=beds,
            meta={"count": len(beds), "schedule": schedule}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reference/baselines", response_model=ApiResponse)
async def get_baselines(
    year: int = Query(2022, description="Baseline year")
):
    """Get clinical baselines by year."""
    try:
        baselines = await ref_repo.get_clinical_baselines(year)
        return ApiResponse(
            data=baselines,
            meta={"count": len(baselines), "year": year}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reference/seasonality", response_model=ApiResponse)
async def get_seasonality(
    year: int = Query(2022, description="Reference year (for context)")
):
    """Get seasonality multipliers."""
    try:
        seasonality = await ref_repo.get_seasonality(year)
        return ApiResponse(
            data=seasonality,
            meta={"count": len(seasonality), "year": year}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reference/staffing-factors", response_model=ApiResponse)
async def get_staffing_factors():
    """Get staffing factors for FTE calculations."""
    try:
        factors = await ref_repo.get_staffing_factors()
        return ApiResponse(
            data=factors,
            meta={"count": len(factors)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Scenario calculation endpoint
@app.post("/scenarios/compute", response_model=ScenarioResponse)
async def compute_scenario(request: ScenarioRequest):
    """Compute scenario results with KPIs and site-level details."""
    try:
        # Validate request
        if not request.sites:
            raise HTTPException(status_code=400, detail="At least one site must be specified")
        
        if request.params.occupancy_target < 0.80:
            raise HTTPException(status_code=400, detail="Occupancy target must be >= 0.80")
        
        # Calculate scenario
        result = await scenario_service.calculate_scenario(request)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "healthcare-scenarios-api"}


# Root endpoint
@app.get("/")
async def root():
    """API root with endpoint information."""
    return {
        "message": "Healthcare Scenarios API",
        "version": settings.api_version,
        "docs": "/docs",
        "endpoints": {
            "reference": {
                "sites": "/reference/sites",
                "programs": "/reference/programs", 
                "staffed_beds": "/reference/staffed-beds",
                "baselines": "/reference/baselines",
                "seasonality": "/reference/seasonality",
                "staffing_factors": "/reference/staffing-factors"
            },
            "scenarios": {
                "compute": "/scenarios/compute"
            }
        }
    }
"""
Main FastAPI application for healthcare scenarios API.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from typing import List, Optional

from .config import settings
from .db import init_db, close_db
from .repositories import ReferenceRepository
from .services import ScenarioService
from .schemas import (
    ApiResponse, PaginatedResponse, ScenarioRequest, ScenarioResponse,
    ErrorResponse
)
import json
from pathlib import Path
import uuid
from datetime import datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    # Allow tests to skip DB init by setting SKIP_DB_INIT=1 in the environment.
    if os.getenv('SKIP_DB_INIT', '0') != '1':
        # Print effective DB connection info for troubleshooting (do not print passwords)
        try:
            print(f"[STARTUP] DB host={settings.mysql_host} port={settings.mysql_port} user={settings.mysql_user}")
        except Exception:
            pass
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

# Repository root (use this rather than Path.cwd() so file operations are consistent
# even when the process current working directory differs, e.g., Codespaces preview)
REPO_ROOT = Path(__file__).resolve().parents[1]


if settings.debug:
    @app.get('/debug/db')
    async def debug_db():
        """Return effective DB connection info (debug only)."""

        # NOTE: Only expose this diagnostic endpoint in debug mode to avoid
        # leaking configuration details in non-development environments.
        if not getattr(settings, 'debug', False):
            raise HTTPException(status_code=404, detail='Not found')

        return {
            'mysql_host': settings.mysql_host,
            'mysql_port': settings.mysql_port,
            'mysql_user': settings.mysql_user,
            'mysql_password_set': bool(settings.mysql_password),
            'env_mysql_user': os.getenv('MYSQL_USER'),
            'env_mysql_password_set': bool(os.getenv('MYSQL_PASSWORD'))
        }


# Add CORS middleware
# Configure CORS. When allow_origins contains '*' we must not set allow_credentials=True
# because browsers will reject Access-Control-Allow-Origin='*' with credentials.
allow_credentials = True
if isinstance(settings.cors_origins, list) and len(settings.cors_origins) == 1 and settings.cors_origins[0] == '*':
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=allow_credentials,
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
        return ApiResponse(data=sites, meta={"count": len(sites)})
    except Exception as e:
        # In dev/test environments the database may be unavailable.
        # Return an empty list so the frontend can still render and show an informative state.
        return ApiResponse(data=[], meta={"count": 0, "error": str(e)})


@app.get("/reference/programs", response_model=ApiResponse)
async def get_programs():
    """Get all healthcare programs."""
    try:
        programs = await ref_repo.get_programs()
        return ApiResponse(data=programs, meta={"count": len(programs)})
    except Exception as e:
        return ApiResponse(data=[], meta={"count": 0, "error": str(e)})


@app.get("/reference/staffed-beds", response_model=ApiResponse)
async def get_staffed_beds(
    schedule: str = Query("Sched-A", description="Schedule code")
):
    """Get staffed beds by schedule."""
    try:
        beds = await ref_repo.get_staffed_beds(schedule)
        return ApiResponse(data=beds, meta={"count": len(beds), "schedule": schedule})
    except Exception as e:
        return ApiResponse(data=[], meta={"count": 0, "error": str(e)})


@app.get("/reference/baselines", response_model=ApiResponse)
async def get_baselines(
    year: int = Query(2022, description="Baseline year")
):
    """Get clinical baselines by year."""
    try:
        baselines = await ref_repo.get_clinical_baselines(year)
        return ApiResponse(data=baselines, meta={"count": len(baselines), "year": year})
    except Exception as e:
        return ApiResponse(data=[], meta={"count": 0, "error": str(e)})


@app.get("/reference/seasonality", response_model=ApiResponse)
async def get_seasonality(
    year: int = Query(2022, description="Reference year (for context)")
):
    """Get seasonality multipliers."""
    try:
        seasonality = await ref_repo.get_seasonality(year)
        return ApiResponse(data=seasonality, meta={"count": len(seasonality), "year": year})
    except Exception as e:
        return ApiResponse(data=[], meta={"count": 0, "error": str(e)})


@app.get("/reference/staffing-factors", response_model=ApiResponse)
async def get_staffing_factors():
    """Get staffing factors for FTE calculations."""
    try:
        factors = await ref_repo.get_staffing_factors()
        return ApiResponse(data=factors, meta={"count": len(factors)})
    except Exception as e:
        return ApiResponse(data=[], meta={"count": 0, "error": str(e)})


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


# Save scenario (simple file-backed persistence for dev/demo)
@app.post("/scenarios/save", response_model=ApiResponse)
async def save_scenario_endpoint(payload: dict):
    """Save a scenario payload to disk and return a save id."""
    try:
        saves_dir = REPO_ROOT / "saved_scenarios"
        saves_dir.mkdir(parents=True, exist_ok=True)

        save_id = uuid.uuid4().hex
        timestamp = datetime.utcnow().isoformat()
        filename = saves_dir / f"scenario_{save_id}.json"

        content = {
            "id": save_id,
            "saved_at": timestamp,
            "payload": payload,
        }

        with filename.open("w", encoding="utf-8") as fh:
            json.dump(content, fh, ensure_ascii=False, indent=2)

        return ApiResponse(data={"id": save_id, "path": str(filename)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")


@app.post('/scenarios/save-label', response_model=ApiResponse)
async def save_scenario_label(label: str = Query(..., description='Label for saved scenario (A/B/C)'), payload: dict = None):
    """Save a scenario under a label (A, B, or C). Overwrites existing labelled saves."""
    try:
        if label not in ('A', 'B', 'C'):
            raise HTTPException(status_code=400, detail='Label must be A, B, or C')

        saves_dir = REPO_ROOT / 'saved_scenarios'
        saves_dir.mkdir(parents=True, exist_ok=True)
        filename = saves_dir / f'scenario_label_{label}.json'

        content = {
            'label': label,
            'saved_at': datetime.utcnow().isoformat(),
            'payload': payload,
        }

        with filename.open('w', encoding='utf-8') as fh:
            json.dump(content, fh, ensure_ascii=False, indent=2)

        return ApiResponse(data={'label': label, 'path': str(filename)})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save-label error: {str(e)}")


@app.get('/scenarios/labels', response_model=ApiResponse)
async def list_labeled_scenarios():
    """Return labelled scenarios A/B/C (dev/demo)."""
    try:
        saves_dir = REPO_ROOT / 'saved_scenarios'
        result = {}
        for label in ('A', 'B', 'C'):
            p = saves_dir / f'scenario_label_{label}.json'
            if p.exists():
                try:
                    with p.open('r', encoding='utf-8') as fh:
                        content = json.load(fh)
                    result[label] = content.get('payload')
                except Exception:
                    result[label] = None
            else:
                result[label] = None

        return ApiResponse(data=result, meta={'count': 3})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'List-labels error: {str(e)}')


@app.get("/scenarios/saved", response_model=ApiResponse)
async def list_saved_scenarios():
    """List saved scenarios from disk (dev/demo only)."""
    try:
        saves_dir = REPO_ROOT / "saved_scenarios"
        if not saves_dir.exists():
            return ApiResponse(data=[], meta={"count": 0})

        entries = []
        for p in sorted(saves_dir.glob('scenario_*.json')):
            try:
                with p.open('r', encoding='utf-8') as fh:
                    content = json.load(fh)
                entries.append({
                    'id': content.get('id'),
                    'saved_at': content.get('saved_at'),
                    'payload': content.get('payload')
                })
            except Exception:
                # skip malformed files
                continue

        return ApiResponse(data=entries, meta={"count": len(entries)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List error: {str(e)}")


@app.post('/scenarios/reset', response_model=ApiResponse)
async def reset_saved_scenarios():
    """Delete all saved scenarios from disk (dev/demo only)."""
    try:
        saves_dir = REPO_ROOT / 'saved_scenarios'
        if not saves_dir.exists():
            return ApiResponse(data={'deleted': 0}, meta={'count': 0})

        deleted = 0
        for p in list(saves_dir.glob('*')):
            try:
                p.unlink()
                deleted += 1
            except Exception:
                # skip files we cannot remove
                continue

        return ApiResponse(data={'deleted': deleted}, meta={'count': deleted})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset error: {str(e)}")


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
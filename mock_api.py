#!/usr/bin/env python3
"""
Simple mock API server for the healthcare scenario planning frontend.
This provides the endpoints expected by the frontend for demonstration purposes.
"""

import json
import random
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Mock data structures
app = FastAPI(
    title="Healthcare Scenarios Mock API",
    description="Mock API for the healthcare scenario planning frontend demo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data - based on the existing data structure
MOCK_SITES = [
    {"site_id": 1, "site_code": "LM-SNW", "site_name": "Snowberry General"},
    {"site_id": 2, "site_code": "LM-BLH", "site_name": "Blue Heron Medical"},
    {"site_id": 3, "site_code": "LM-SRC", "site_name": "Salmon Run Hospital"},
    {"site_id": 4, "site_code": "LM-MSC", "site_name": "Mossy Cedar Community"},
    {"site_id": 5, "site_code": "LM-OTB", "site_name": "Otter Bay Medical Ctr"},
    {"site_id": 6, "site_code": "LM-BRC", "site_name": "Bear Creek Hospital"},
    {"site_id": 7, "site_code": "LM-DFT", "site_name": "Driftwood Regional"},
    {"site_id": 8, "site_code": "LM-STG", "site_name": "Stargazer Hlth Ctr"},
    {"site_id": 9, "site_code": "LM-SRC", "site_name": "Sunrise Coast Hosp"},
    {"site_id": 10, "site_code": "LM-GRS", "site_name": "Grouse Ridge Medical"},
    {"site_id": 11, "site_code": "LM-FGH", "site_name": "Foggy Harbor Hosp"},
    {"site_id": 12, "site_code": "LM-GPK", "site_name": "Granite Peak Medical"},
]

MOCK_PROGRAMS = [
    {"program_id": 1, "program_name": "Medicine"},
    {"program_id": 2, "program_name": "Inpatient MHSU"},
    {"program_id": 3, "program_name": "MICY"},
    {"program_id": 4, "program_name": "Critical Care"},
    {"program_id": 5, "program_name": "Surgery / Periop"},
    {"program_id": 6, "program_name": "Emergency"},
]

MOCK_SUBPROGRAMS = [
    {"program_id": 1, "subprogram_id": 1, "subprogram_name": "General Medicine"},
    {"program_id": 1, "subprogram_id": 2, "subprogram_name": "ACE Unit"},
    {"program_id": 1, "subprogram_id": 3, "subprogram_name": "Hospitalist"},
    {"program_id": 2, "subprogram_id": 1, "subprogram_name": "Adult Mental Health"},
    {"program_id": 2, "subprogram_id": 2, "subprogram_name": "Substance Use"},
    {"program_id": 2, "subprogram_id": 3, "subprogram_name": "Concurrent Disorders"},
]

# Request/Response models
class ScenarioParams(BaseModel):
    occupancy_target: float
    los_delta: float
    alc_target: float
    growth_pct: float
    schedule_code: str = "Sched-A"
    seasonality: bool = False

class ScenarioRequest(BaseModel):
    sites: List[int]
    program_id: int
    baseline_year: int = 2022
    horizon_years: int = 3
    params: ScenarioParams

# API endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Healthcare Scenarios Mock API"}

@app.get("/reference/sites")
def get_sites():
    return MOCK_SITES

@app.get("/reference/programs")
def get_programs():
    return MOCK_PROGRAMS

@app.get("/reference/subprograms")
def get_subprograms(program_id: int = None):
    if program_id:
        return [sp for sp in MOCK_SUBPROGRAMS if sp["program_id"] == program_id]
    return MOCK_SUBPROGRAMS

@app.get("/reference/staffed-beds")
def get_staffed_beds(schedule: str = "Sched-A"):
    # Mock staffed beds data
    mock_data = []
    for site in MOCK_SITES:
        for program in MOCK_PROGRAMS:
            mock_data.append({
                "id": len(mock_data) + 1,
                "site_id": site["site_id"],
                "program_id": program["program_id"],
                "schedule_code": schedule,
                "staffed_beds": random.randint(20, 100)
            })
    return mock_data

@app.get("/reference/baselines")
def get_baselines(year: int = 2022):
    # Mock baseline data
    mock_data = []
    for site in MOCK_SITES:
        for program in MOCK_PROGRAMS:
            mock_data.append({
                "id": len(mock_data) + 1,
                "site_id": site["site_id"],
                "program_id": program["program_id"],
                "baseline_year": year,
                "los_base_days": round(random.uniform(3.0, 12.0), 1),
                "alc_rate": round(random.uniform(0.10, 0.20), 2)
            })
    return mock_data

@app.get("/reference/seasonality")
def get_seasonality(year: int = 2022):
    # Mock seasonality data
    return [
        {"id": i, "site_id": None, "program_id": None, "month": i, "multiplier": round(random.uniform(0.9, 1.1), 2)}
        for i in range(1, 13)
    ]

@app.get("/reference/staffing-factors")
def get_staffing_factors():
    # Mock staffing factors
    return [
        {"id": i, "program_id": i, "subprogram_id": None, "hppd": round(random.uniform(4.0, 8.0), 1), 
         "annual_hours_per_fte": 1950, "productivity_factor": 0.85}
        for i in range(1, 7)
    ]

@app.post("/scenarios/compute")
def calculate_scenario(request: ScenarioRequest):
    """Calculate a scenario and return mock results"""
    
    # Mock calculation based on request parameters
    total_sites = len(request.sites)
    site_results = []
    
    for site_id in request.sites:
        site = next(s for s in MOCK_SITES if s["site_id"] == site_id)
        
        # Mock calculations with some realistic variation
        base_admissions = random.randint(800, 1200)
        admissions_projected = int(base_admissions * (1 + request.params.growth_pct))
        
        los_effective = round(random.uniform(4.0, 8.0) * (1 + request.params.los_delta), 1)
        patient_days = int(admissions_projected * los_effective)
        census_average = round(patient_days / 365, 1)
        required_beds = int(census_average / request.params.occupancy_target)
        staffed_beds = random.randint(60, 90)
        capacity_gap = required_beds - staffed_beds
        nursing_fte = round(required_beds * random.uniform(5.0, 7.0), 1)
        
        site_results.append({
            "site_id": site_id,
            "site_code": site["site_code"],
            "site_name": site["site_name"],
            "admissions_projected": admissions_projected,
            "los_effective": los_effective,
            "patient_days": patient_days,
            "census_average": census_average,
            "required_beds": required_beds,
            "staffed_beds": staffed_beds,
            "capacity_gap": capacity_gap,
            "nursing_fte": nursing_fte
        })
    
    # Calculate aggregate KPIs
    total_required_beds = sum(r["required_beds"] for r in site_results)
    total_staffed_beds = sum(r["staffed_beds"] for r in site_results)
    total_capacity_gap = total_required_beds - total_staffed_beds
    total_nursing_fte = sum(r["nursing_fte"] for r in site_results)
    avg_occupancy = request.params.occupancy_target
    total_admissions = sum(r["admissions_projected"] for r in site_results)
    avg_los_effective = sum(r["los_effective"] for r in site_results) / len(site_results)
    
    return {
        "kpis": {
            "total_required_beds": total_required_beds,
            "total_staffed_beds": total_staffed_beds,
            "total_capacity_gap": total_capacity_gap,
            "total_nursing_fte": round(total_nursing_fte, 1),
            "avg_occupancy": avg_occupancy,
            "total_admissions": total_admissions,
            "avg_los_effective": round(avg_los_effective, 1)
        },
        "by_site": site_results,
        "metadata": {
            "calculation_time": "2025-01-21T18:00:00Z",
            "baseline_year": request.baseline_year,
            "horizon_years": request.horizon_years,
            "parameters": request.params.dict()
        }
    }

# Additional endpoints for completeness
@app.get("/facilities/summary")
def get_facilities_summary():
    return {
        "total_sites": len(MOCK_SITES),
        "total_programs": len(MOCK_PROGRAMS),
        "total_beds": sum(random.randint(50, 100) for _ in MOCK_SITES),
        "avg_occupancy": 0.85
    }

@app.get("/patients")
def get_patients(page: int = 1, pageSize: int = 10, q: str = None):
    # Mock patient data
    mock_patients = [
        {
            "patient_id": i,
            "age": random.randint(18, 90),
            "gender": random.choice(["Male", "Female", "Other"]),
            "home_lha": random.choice(["Harborview", "Riverbend", "North Shoreline"]),
            "facility_site_code": random.choice([s["site_code"] for s in MOCK_SITES[:3]]),
            "admission_date": "2024-01-15"
        }
        for i in range(1, 101)
    ]
    
    start = (page - 1) * pageSize
    end = start + pageSize
    
    return {
        "data": mock_patients[start:end],
        "meta": {
            "total": len(mock_patients),
            "page": page,
            "pageSize": pageSize,
            "totalPages": (len(mock_patients) + pageSize - 1) // pageSize
        }
    }

@app.get("/ed/projections")
def get_ed_projections(year: int, method: str = None):
    # Mock ED projections
    return [
        {
            "year": year,
            "month": month,
            "value": random.randint(800, 1200),
            "metric": "ed_visits",
            "site_code": "LM-SNW"
        }
        for month in range(1, 13)
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
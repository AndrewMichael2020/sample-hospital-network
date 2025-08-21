"""
FastAPI application for the synthetic healthcare data API.
Implements instructions 01, 02, 03: API endpoints for dimension data, 
population projections, and patient/encounter data.
"""

import os
import pandas as pd
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api_models import (
    # Enums
    AgeGroup, Gender, EDSubservice, Acuity, Disposition,
    # Dimension models (Instruction 01)
    DimSite, DimProgram, DimSubprogram, DimLHA,
    # Population models (Instruction 02)
    PopulationProjection, EDBaselineRate,
    # Patient models (Instruction 03)
    Patient, EDEncounter, IPStay,
    # Response models
    APIResponse, PaginationParams, FilterParams,
    ValidationResult, DataQualityMetrics
)


# Initialize FastAPI app
app = FastAPI(
    title="Synthetic Healthcare Data API",
    description="REST API for accessing synthetic healthcare data from the Lower Mainland hospital network",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory path
DATA_DIR = "./data"


# Helper functions
def load_csv_data(filename: str) -> pd.DataFrame:
    """Load CSV data file and handle errors."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Data file {filename} not found")
    
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


def paginate_dataframe(df: pd.DataFrame, page: int, size: int) -> tuple:
    """Paginate a DataFrame and return data with metadata."""
    total_records = len(df)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    paginated_df = df.iloc[start_idx:end_idx]
    
    return paginated_df, total_records


def apply_filters(df: pd.DataFrame, filters: FilterParams) -> pd.DataFrame:
    """Apply common filters to a DataFrame."""
    if filters.facility_id is not None:
        if 'facility_id' in df.columns:
            df = df[df['facility_id'] == filters.facility_id]
        elif 'facility_home_id' in df.columns:
            df = df[df['facility_home_id'] == filters.facility_id]
    
    if filters.lha_id is not None and 'lha_id' in df.columns:
        df = df[df['lha_id'] == filters.lha_id]
    
    if filters.age_group is not None and 'age_group' in df.columns:
        df = df[df['age_group'] == filters.age_group.value]
    
    if filters.gender is not None and 'gender' in df.columns:
        df = df[df['gender'] == filters.gender.value]
    
    if filters.year is not None and 'year' in df.columns:
        df = df[df['year'] == filters.year]
    
    return df


# Root endpoint
@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information."""
    return APIResponse(
        message="Synthetic Healthcare Data API - Lower Mainland Hospital Network",
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "dimensions": "/api/v1/dimensions/",
                "population": "/api/v1/population/",
                "patients": "/api/v1/patients/",
                "validation": "/api/v1/validation/"
            }
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Instruction 01: Dimension Data API Endpoints

@app.get("/api/v1/dimensions/sites", response_model=APIResponse)
async def get_sites(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get hospital facility dimension data."""
    df = load_csv_data("dim_site.csv")
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    sites = []
    for idx, row in paginated_df.iterrows():
        sites.append(DimSite(
            site_id=idx + 1,  # Use index + 1 as site_id since it's not in CSV
            site_code=row['site_code'],
            site_name=row['site_name'],
            site_type='Hospital'  # Default value
        ))
    
    return APIResponse(
        message="Sites retrieved successfully",
        data=sites,
        count=len(sites)
    )


@app.get("/api/v1/dimensions/programs", response_model=APIResponse)
async def get_programs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get healthcare program dimension data."""
    df = load_csv_data("dim_program.csv")
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    programs = []
    for _, row in paginated_df.iterrows():
        programs.append(DimProgram(
            program_id=int(row['program_id']),
            program_name=row['program_name'],
            program_category='Clinical'  # Default value
        ))
    
    return APIResponse(
        message="Programs retrieved successfully",
        data=programs,
        count=len(programs)
    )


@app.get("/api/v1/dimensions/subprograms", response_model=APIResponse)
async def get_subprograms(
    program_id: Optional[int] = Query(None, description="Filter by program ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get healthcare subprogram dimension data."""
    df = load_csv_data("dim_subprogram.csv")
    
    if program_id is not None:
        df = df[df['program_id'] == program_id]
    
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    subprograms = []
    for _, row in paginated_df.iterrows():
        subprograms.append(DimSubprogram(
            subprogram_id=int(row['subprogram_id']),
            program_id=int(row['program_id']),
            subprogram_name=row['subprogram_name']
        ))
    
    return APIResponse(
        message="Subprograms retrieved successfully",
        data=subprograms,
        count=len(subprograms)
    )


@app.get("/api/v1/dimensions/lhas", response_model=APIResponse)
async def get_lhas(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get Local Health Area dimension data."""
    df = load_csv_data("dim_lha.csv")
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    lhas = []
    for idx, row in paginated_df.iterrows():
        lhas.append(DimLHA(
            lha_id=idx + 1,  # Use index + 1 as lha_id since it's not in CSV
            lha_name=row['lha_name'],
            default_site_id=int(row['default_site_id'])
        ))
    
    return APIResponse(
        message="LHAs retrieved successfully",
        data=lhas,
        count=len(lhas)
    )


# Instruction 02: Population and Rates API Endpoints

@app.get("/api/v1/population/projections", response_model=APIResponse)
async def get_population_projections(
    filters: FilterParams = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get population projection data."""
    df = load_csv_data("population_projection.csv")
    df = apply_filters(df, filters)
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    projections = []
    for _, row in paginated_df.iterrows():
        projections.append(PopulationProjection(
            year=int(row['year']),
            lha_id=int(row['lha_id']),
            age_group=AgeGroup(row['age_group']),
            gender=Gender(row['gender']),
            population=int(row['population'])
        ))
    
    return APIResponse(
        message="Population projections retrieved successfully",
        data=projections,
        count=len(projections)
    )


@app.get("/api/v1/population/ed-rates", response_model=APIResponse)
async def get_ed_baseline_rates(
    filters: FilterParams = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get Emergency Department baseline utilization rates."""
    df = load_csv_data("ed_baseline_rates.csv")
    df = apply_filters(df, filters)
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    rates = []
    for _, row in paginated_df.iterrows():
        rates.append(EDBaselineRate(
            lha_id=int(row['lha_id']),
            age_group=AgeGroup(row['age_group']),
            gender=Gender(row['gender']),
            ed_subservice=EDSubservice(row['ed_subservice']),
            baserate_per_1000=float(row['baserate_per_1000'])
        ))
    
    return APIResponse(
        message="ED baseline rates retrieved successfully",
        data=rates,
        count=len(rates)
    )


# Instruction 03: Patient and Encounter API Endpoints

@app.get("/api/v1/patients", response_model=APIResponse)
async def get_patients(
    filters: FilterParams = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get patient demographic data."""
    df = load_csv_data("patients.csv")
    df = apply_filters(df, filters)
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    patients = []
    for _, row in paginated_df.iterrows():
        # Convert date string to date object
        dob = pd.to_datetime(row['dob']).date()
        
        patients.append(Patient(
            patient_id=row['patient_id'],
            dob=dob,
            age_group=AgeGroup(row['age_group']),
            gender=Gender(row['gender']),
            lha_id=int(row['lha_id']),
            facility_home_id=int(row['facility_home_id']),
            primary_ed_subservice=EDSubservice(row['primary_ed_subservice']),
            ed_visits_year=int(row['ed_visits_year'])
        ))
    
    return APIResponse(
        message="Patients retrieved successfully",
        data=patients,
        count=len(patients)
    )


@app.get("/api/v1/encounters/ed", response_model=APIResponse)
async def get_ed_encounters(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    filters: FilterParams = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get Emergency Department encounter data."""
    df = load_csv_data("ed_encounters.csv")
    
    if patient_id:
        df = df[df['patient_id'] == patient_id]
    
    df = apply_filters(df, filters)
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    encounters = []
    for _, row in paginated_df.iterrows():
        # Convert timestamp string to datetime object
        arrival_timestamp = pd.to_datetime(row['arrival_ts'])
        
        encounters.append(EDEncounter(
            encounter_id=int(row['encounter_id']),
            patient_id=row['patient_id'],
            facility_id=int(row['facility_id']),
            ed_subservice=EDSubservice(row['ed_subservice']),
            arrival_timestamp=arrival_timestamp,
            acuity=Acuity(int(row['acuity'])),
            disposition=Disposition(row['dispo'])
        ))
    
    return APIResponse(
        message="ED encounters retrieved successfully",
        data=encounters,
        count=len(encounters)
    )


@app.get("/api/v1/encounters/ip", response_model=APIResponse)
async def get_ip_stays(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    filters: FilterParams = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get inpatient stay data."""
    df = load_csv_data("ip_stays.csv")
    
    if patient_id:
        df = df[df['patient_id'] == patient_id]
    
    df = apply_filters(df, filters)
    paginated_df, total_records = paginate_dataframe(df, page, size)
    
    stays = []
    for _, row in paginated_df.iterrows():
        # Convert timestamp strings to datetime objects
        admit_timestamp = pd.to_datetime(row['admit_ts'])
        discharge_timestamp = None
        if pd.notna(row['discharge_ts']):
            discharge_timestamp = pd.to_datetime(row['discharge_ts'])
        
        stays.append(IPStay(
            stay_id=int(row['stay_id']),
            patient_id=row['patient_id'],
            facility_id=int(row['facility_id']),
            program_id=int(row['program_id']),
            subprogram_id=int(row['subprogram_id']),
            admit_timestamp=admit_timestamp,
            discharge_timestamp=discharge_timestamp,
            los_days=float(row['los_days']) if pd.notna(row['los_days']) else None,
            alc_flag=bool(row['alc_flag'])
        ))
    
    return APIResponse(
        message="IP stays retrieved successfully",
        data=stays,
        count=len(stays)
    )


# Data validation endpoints
@app.get("/api/v1/validation/summary", response_model=APIResponse)
async def get_validation_summary():
    """Get data validation summary."""
    try:
        # Simple validation - check if all required files exist and have data
        required_files = [
            "dim_site.csv", "dim_program.csv", "dim_subprogram.csv", "dim_lha.csv",
            "population_projection.csv", "ed_baseline_rates.csv",
            "patients.csv", "ed_encounters.csv", "ip_stays.csv"
        ]
        
        validation_results = []
        overall_passed = True
        
        for filename in required_files:
            try:
                df = load_csv_data(filename)
                record_count = len(df)
                passed = record_count > 0
                
                validation_results.append({
                    "file": filename,
                    "passed": passed,
                    "record_count": record_count,
                    "errors": [] if passed else [f"File {filename} has no records"]
                })
                
                if not passed:
                    overall_passed = False
                    
            except Exception as e:
                validation_results.append({
                    "file": filename,
                    "passed": False,
                    "record_count": 0,
                    "errors": [str(e)]
                })
                overall_passed = False
        
        return APIResponse(
            message="Validation summary retrieved successfully",
            data=ValidationResult(
                passed=overall_passed,
                details={"file_validations": validation_results}
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "Endpoint not found", "data": None}
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "data": None}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
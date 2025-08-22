"""
Pydantic schemas for the extended API.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import model_validator
from pydantic import BaseModel, Field
from decimal import Decimal


# Base response models
class ApiResponse(BaseModel):
    """Standard API response format."""
    data: Any
    meta: Dict[str, Any] = Field(default_factory=dict)


class PaginatedResponse(BaseModel):
    """Paginated API response format.""" 
    data: List[Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


# Reference table models
class StaffedBedsSchedule(BaseModel):
    """Staffed beds schedule model."""
    id: int
    site_id: int
    program_id: int
    schedule_code: str
    staffed_beds: int


class ClinicalBaseline(BaseModel):
    """Clinical baseline model."""
    id: int
    site_id: int
    program_id: int
    baseline_year: int
    los_base_days: float
    alc_rate: float


class SeasonalityMonthly(BaseModel):
    """Seasonality monthly model."""
    id: int
    site_id: Optional[int]
    program_id: Optional[int]
    month: int
    multiplier: float


class StaffingFactor(BaseModel):
    """Staffing factor model."""
    id: int
    program_id: int
    subprogram_id: Optional[int]
    hppd: float
    annual_hours_per_fte: int
    productivity_factor: float


# Dimension models (for reference endpoints)
class Site(BaseModel):
    """Site dimension model."""
    site_id: int
    site_code: str
    site_name: str


class Program(BaseModel):
    """Program dimension model."""
    program_id: int
    program_name: str


class Subprogram(BaseModel):
    """Subprogram dimension model."""
    program_id: int
    subprogram_id: int
    subprogram_name: str


# Scenario calculation models
class ScenarioParams(BaseModel):
    """Parameters for scenario calculations."""
    occupancy_target: float = Field(..., ge=0.80, le=1.0, description="Target occupancy rate")
    los_delta: float = Field(0.0, ge=-0.50, le=0.50, description="LOS change percentage")
    alc_target: float = Field(..., ge=0.0, le=0.50, description="Target ALC rate")
    growth_pct: float = Field(0.0, ge=-0.20, le=0.20, description="Annual growth percentage")
    schedule_code: str = Field("Sched-A", description="Capacity schedule code")
    seasonality: bool = Field(False, description="Apply seasonality adjustments")


class ScenarioRequest(BaseModel):
    """Request for scenario calculation."""
    sites: List[int] = Field(..., description="Site IDs to include")
    # Backwards-compatible: either provide a single `program_id` or a
    # list `program_ids`. Internally we normalize to `program_ids`.
    program_id: Optional[int] = Field(None, description="Program ID (deprecated, use program_ids)")
    program_ids: Optional[List[int]] = Field(None, description="List of Program IDs to include in the calculation")
    baseline_year: int = Field(2022, description="Baseline year")
    horizon_years: int = Field(3, description="Planning horizon in years")
    params: ScenarioParams

    @model_validator(mode='before')
    def ensure_program_ids(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # If caller provided program_id but not program_ids, normalize to program_ids
        pid = values.get('program_id')
        pids = values.get('program_ids')
        if not pids and pid is None:
            raise ValueError('Either program_id or program_ids must be provided')
        if not pids and pid is not None:
            values['program_ids'] = [pid]
        # If program_ids provided but program_id missing, keep program_id as the first value
        if pids and not pid:
            try:
                values['program_id'] = pids[0]
            except Exception:
                pass
        return values


class SiteResult(BaseModel):
    """Results for a single site."""
    site_id: int
    site_code: str
    site_name: str
    admissions_projected: int
    los_effective: float
    patient_days: int
    census_average: float
    required_beds: int
    staffed_beds: int
    capacity_gap: int
    nursing_fte: Optional[float] = None


class ScenarioKPIs(BaseModel):
    """Aggregate scenario KPIs."""
    total_required_beds: int
    total_staffed_beds: int
    total_capacity_gap: int
    total_nursing_fte: Optional[float] = None
    avg_occupancy: float
    total_admissions: int
    avg_los_effective: float


class ScenarioResponse(BaseModel):
    """Response for scenario calculation."""
    kpis: ScenarioKPIs
    by_site: List[SiteResult]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Error models
class ErrorDetail(BaseModel):
    """Error detail model."""
    type: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model.""" 
    error: str
    details: List[ErrorDetail] = Field(default_factory=list)
    request_id: Optional[str] = None
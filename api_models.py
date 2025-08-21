"""
Pydantic models for the healthcare data API.
Implements instruction 00: Config & Pydantic models for data validation and API responses.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class AgeGroup(str, Enum):
    """Age group categories used in the healthcare system."""
    AGE_0_4 = "0-4"
    AGE_5_14 = "5-14"
    AGE_15_24 = "15-24"
    AGE_25_44 = "25-44"
    AGE_45_64 = "45-64"
    AGE_65_74 = "65-74"
    AGE_75_84 = "75-84"
    AGE_85_PLUS = "85+"


class Gender(str, Enum):
    """Gender categories."""
    FEMALE = "Female"
    MALE = "Male"
    OTHER = "Other"


class EDSubservice(str, Enum):
    """Emergency Department subservice types."""
    ADULT_ED = "Adult ED"
    PEDIATRIC_ED = "Pediatric ED"
    URGENT_CARE = "Urgent Care Centre"


class Acuity(int, Enum):
    """ED acuity levels (1=most urgent, 5=least urgent)."""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


class Disposition(str, Enum):
    """ED encounter disposition."""
    DISCHARGED = "Discharged"
    ADMITTED = "Admitted"
    TRANSFERRED = "Transferred"
    LEFT_WITHOUT_BEING_SEEN = "LWBS"


# Dimension Models (Instruction 01)

class DimSite(BaseModel):
    """Hospital facility dimension."""
    site_id: int = Field(..., description="Unique facility identifier")
    site_code: str = Field(..., description="Facility code (e.g., LM-SNW)")
    site_name: str = Field(..., description="Facility name")
    site_type: str = Field(default="Hospital", description="Type of facility")


class DimProgram(BaseModel):
    """Healthcare program dimension."""
    program_id: int = Field(..., description="Unique program identifier")
    program_name: str = Field(..., description="Program name (e.g., Medicine, Surgery)")
    program_category: str = Field(default="Clinical", description="Program category")


class DimSubprogram(BaseModel):
    """Healthcare subprogram dimension."""
    subprogram_id: int = Field(..., description="Unique subprogram identifier")
    program_id: int = Field(..., description="Parent program identifier")
    subprogram_name: str = Field(..., description="Subprogram name")


class DimLHA(BaseModel):
    """Local Health Area dimension."""
    lha_id: int = Field(..., description="Unique LHA identifier")
    lha_name: str = Field(..., description="LHA name (e.g., Harborview)")
    default_site_id: int = Field(..., description="Default facility for this LHA")


# Population and Rates Models (Instruction 02)

class PopulationProjection(BaseModel):
    """Population projection data."""
    year: int = Field(..., description="Projection year")
    lha_id: int = Field(..., description="Local Health Area identifier")
    age_group: AgeGroup = Field(..., description="Age group")
    gender: Gender = Field(..., description="Gender")
    population: int = Field(..., description="Projected population count")


class EDBaselineRate(BaseModel):
    """Emergency Department baseline utilization rates."""
    lha_id: int = Field(..., description="Local Health Area identifier")
    age_group: AgeGroup = Field(..., description="Age group")
    gender: Gender = Field(..., description="Gender")
    ed_subservice: EDSubservice = Field(..., description="ED subservice type")
    baserate_per_1000: float = Field(..., description="Baseline rate per 1000 population per year")


# Patient and Encounter Models (Instruction 03)

class Patient(BaseModel):
    """Patient demographic information."""
    patient_id: str = Field(..., description="Unique patient identifier")
    dob: date = Field(..., description="Date of birth")
    age_group: AgeGroup = Field(..., description="Age group category")
    gender: Gender = Field(..., description="Gender")
    lha_id: int = Field(..., description="Home Local Health Area")
    facility_home_id: int = Field(..., description="Home facility identifier")
    primary_ed_subservice: EDSubservice = Field(..., description="Primary ED service for this patient")
    ed_visits_year: int = Field(..., description="Expected ED visits per year")


class EDEncounter(BaseModel):
    """Emergency Department encounter."""
    encounter_id: int = Field(..., description="Unique encounter identifier")
    patient_id: str = Field(..., description="Patient identifier")
    facility_id: int = Field(..., description="Facility where encounter occurred")
    ed_subservice: EDSubservice = Field(..., description="ED subservice")
    arrival_timestamp: datetime = Field(..., description="Arrival timestamp")
    acuity: Acuity = Field(..., description="Acuity level (1=most urgent)")
    disposition: Disposition = Field(..., description="Encounter disposition")


class IPStay(BaseModel):
    """Inpatient stay record."""
    stay_id: int = Field(..., description="Unique stay identifier")
    patient_id: str = Field(..., description="Patient identifier")
    facility_id: int = Field(..., description="Facility identifier")
    program_id: int = Field(..., description="Program identifier")
    subprogram_id: int = Field(..., description="Subprogram identifier")
    admit_timestamp: datetime = Field(..., description="Admission timestamp")
    discharge_timestamp: Optional[datetime] = Field(None, description="Discharge timestamp")
    los_days: Optional[float] = Field(None, description="Length of stay in days")
    alc_flag: bool = Field(default=False, description="Alternate Level of Care flag")


# API Response Models

class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = Field(default=True, description="Request success status")
    message: str = Field(default="OK", description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    count: Optional[int] = Field(None, description="Number of records returned")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(50, ge=1, le=1000, description="Page size (max 1000)")


class FilterParams(BaseModel):
    """Common filter parameters."""
    facility_id: Optional[int] = Field(None, description="Filter by facility")
    lha_id: Optional[int] = Field(None, description="Filter by LHA")
    age_group: Optional[AgeGroup] = Field(None, description="Filter by age group")
    gender: Optional[Gender] = Field(None, description="Filter by gender")
    year: Optional[int] = Field(None, description="Filter by year")


# Validation Models

class ValidationResult(BaseModel):
    """Data validation result."""
    passed: bool = Field(..., description="Whether validation passed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Validation details")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class DataQualityMetrics(BaseModel):
    """Data quality metrics."""
    total_records: int = Field(..., description="Total number of records")
    completeness_score: float = Field(..., ge=0, le=1, description="Data completeness score")
    consistency_score: float = Field(..., ge=0, le=1, description="Data consistency score")
    validity_score: float = Field(..., ge=0, le=1, description="Data validity score")
    overall_quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
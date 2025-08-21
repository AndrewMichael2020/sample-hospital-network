"""
Business logic service layer for scenario calculations.
Implements the compute model from the specification.
"""

import math
from typing import List, Dict, Any, Optional
from .repositories import ScenarioRepository, ReferenceRepository
from .schemas import ScenarioRequest, ScenarioResponse, ScenarioKPIs, SiteResult


class ScenarioService:
    """Service for scenario calculations."""
    
    def __init__(self):
        self.scenario_repo = ScenarioRepository()
        self.ref_repo = ReferenceRepository()
    
    async def calculate_scenario(self, request: ScenarioRequest) -> ScenarioResponse:
        """Calculate scenario results for given parameters."""
        
        # Get baseline data for all sites
        baselines = await self.scenario_repo.get_site_program_baseline(
            request.sites, request.program_id, request.baseline_year
        )
        
        # Get staffed beds for all sites
        staffed_beds = await self.scenario_repo.get_site_staffed_beds(
            request.sites, request.program_id, request.params.schedule_code
        )
        
        # Get baseline admissions from historical data
        historical_admissions = await self.scenario_repo.get_baseline_admissions(
            request.sites, request.program_id, request.baseline_year
        )
        
        # Get staffing factor for FTE calculations
        staffing_factor = await self.scenario_repo.get_staffing_factor(request.program_id)
        
        # Calculate results for each site
        site_results = []
        total_required_beds = 0
        total_staffed_beds = 0
        total_admissions = 0
        total_patient_days = 0
        total_fte = 0.0 if staffing_factor else None
        
        for site_id in request.sites:
            site_result = await self._calculate_site_result(
                site_id, request, baselines, staffed_beds, 
                historical_admissions, staffing_factor
            )
            
            if site_result:
                site_results.append(site_result)
                total_required_beds += site_result.required_beds
                total_staffed_beds += site_result.staffed_beds
                total_admissions += site_result.admissions_projected
                total_patient_days += site_result.patient_days
                
                if site_result.nursing_fte:
                    total_fte = (total_fte or 0) + site_result.nursing_fte
        
        # Calculate aggregate KPIs
        avg_occupancy = total_patient_days / (total_staffed_beds * 365) if total_staffed_beds > 0 else 0
        avg_los_effective = total_patient_days / total_admissions if total_admissions > 0 else 0
        
        kpis = ScenarioKPIs(
            total_required_beds=total_required_beds,
            total_staffed_beds=total_staffed_beds, 
            total_capacity_gap=total_required_beds - total_staffed_beds,
            total_nursing_fte=total_fte,
            avg_occupancy=round(avg_occupancy, 3),
            total_admissions=total_admissions,
            avg_los_effective=round(avg_los_effective, 2)
        )
        
        return ScenarioResponse(
            kpis=kpis,
            by_site=site_results,
            metadata={
                "request_params": request.model_dump(),
                "calculation_date": "2025-01-01",  # Would be datetime.now() in real implementation
                "model_version": "1.0"
            }
        )
    
    async def _calculate_site_result(
        self,
        site_id: int,
        request: ScenarioRequest,
        baselines: List[Dict],
        staffed_beds: List[Dict],
        historical_admissions: List[Dict], 
        staffing_factor: Optional[Dict]
    ) -> Optional[SiteResult]:
        """Calculate results for a single site."""
        
        # Find baseline data for this site
        site_baseline = next((b for b in baselines if b['site_id'] == site_id), None)
        if not site_baseline:
            return None
        
        # Find staffed beds for this site
        site_beds = next((s for s in staffed_beds if s['site_id'] == site_id), None)
        if not site_beds:
            return None
        
        # Find historical admissions (fallback if not available)
        site_admissions = next((a for a in historical_admissions if a['site_id'] == site_id), None)
        baseline_admissions = site_admissions['admissions_base'] if site_admissions else 100
        
        # Apply the compute model
        g = request.params.growth_pct
        y = request.horizon_years
        d = request.params.los_delta
        occ_t = request.params.occupancy_target
        alc_t = request.params.alc_target
        alc_b = site_baseline['alc_rate']
        los_b = site_baseline['los_base_days']
        
        # Calculate projections
        admissions_projected = int(baseline_admissions * ((1 + g) ** y))
        los_acute = los_b * (1 + d)
        los_effective = los_acute * (1 + (alc_t - alc_b))
        
        # Apply bounds/guards
        los_effective = max(0.25, los_effective)
        
        # Get seasonality multiplier (using average of year)
        seasonality_factor = 1.0
        if request.params.seasonality:
            seasonality_factor = await self._get_average_seasonality(
                site_id, request.program_id
            )
        
        patient_days = int(admissions_projected * los_effective * seasonality_factor)
        census_average = patient_days / 365
        required_beds = math.ceil(census_average / occ_t)
        
        # Calculate nursing FTE if staffing factors available
        nursing_fte = None
        if staffing_factor:
            hppd = staffing_factor['hppd']
            annual_hours = staffing_factor['annual_hours_per_fte']
            productivity = staffing_factor['productivity_factor']
            
            total_hours_needed = required_beds * hppd * 365
            nursing_fte = total_hours_needed / (annual_hours * productivity)
            nursing_fte = round(nursing_fte, 1)
        
        return SiteResult(
            site_id=site_id,
            site_code=site_baseline['site_code'],
            site_name=site_baseline['site_name'],
            admissions_projected=admissions_projected,
            los_effective=round(los_effective, 2),
            patient_days=patient_days,
            census_average=round(census_average, 1),
            required_beds=required_beds,
            staffed_beds=site_beds['staffed_beds'],
            capacity_gap=required_beds - site_beds['staffed_beds'],
            nursing_fte=nursing_fte
        )
    
    async def _get_average_seasonality(
        self, 
        site_id: int, 
        program_id: int
    ) -> float:
        """Calculate average seasonality factor across all months."""
        total = 0.0
        for month in range(1, 13):
            multiplier = await self.scenario_repo.get_seasonality_multiplier(
                site_id, program_id, month
            )
            total += multiplier
        return total / 12
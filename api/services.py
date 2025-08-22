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
        
        # Normalize program ids (request.program_ids ensured by schema validator)
        program_ids = getattr(request, 'program_ids', [request.program_id]) or [request.program_id]

        # Fetch data for all program_ids and aggregate where appropriate
        baselines = []
        staffed_beds = []
        historical_admissions = []
        staffing_factors = {}

        for pid in program_ids:
            b = await self.scenario_repo.get_site_program_baseline(request.sites, pid, request.baseline_year)
            baselines.extend(b or [])

            sb = await self.scenario_repo.get_site_staffed_beds(request.sites, pid, request.params.schedule_code)
            staffed_beds.extend(sb or [])

            ha = await self.scenario_repo.get_baseline_admissions(request.sites, pid, request.baseline_year)
            historical_admissions.extend(ha or [])

            sf = await self.scenario_repo.get_staffing_factor(pid)
            if sf:
                staffing_factors[pid] = sf
        
        # Calculate results for each site
        site_results = []
        total_required_beds = 0
        total_staffed_beds = 0
        total_admissions = 0
        total_patient_days = 0
        overall_total_fte = 0.0 if staffing_factors else None
        
        for site_id in request.sites:
            per_program_results = []
            total_staffed_for_site = 0
            total_required = 0
            total_adm = 0
            total_days = 0
            site_total_fte = 0.0
            fte_count = 0

            for pid in program_ids:
                sf = staffing_factors.get(pid)
                b = [x for x in baselines if x.get('site_id') == site_id and x.get('program_id') == pid]
                sb = [x for x in staffed_beds if x.get('site_id') == site_id and x.get('program_id') == pid]
                ha = [x for x in historical_admissions if x.get('site_id') == site_id and x.get('program_id') == pid]

                class _Req:
                    pass
                pr = _Req()
                pr.sites = [site_id]
                pr.program_id = pid
                pr.program_ids = program_ids
                pr.baseline_year = request.baseline_year
                pr.horizon_years = request.horizon_years
                pr.params = request.params

                site_res = await self._calculate_site_result(site_id, pr, b, sb, ha, sf)
                if site_res:
                    per_program_results.append(site_res)
                    total_required += site_res.required_beds
                    total_staffed_for_site += site_res.staffed_beds
                    total_adm += site_res.admissions_projected
                    total_days += site_res.patient_days
                    if site_res.nursing_fte:
                        site_total_fte += site_res.nursing_fte
                        fte_count += 1

            if not per_program_results:
                continue

            aggregated = SiteResult(
                site_id=site_id,
                site_code=per_program_results[0].site_code,
                site_name=per_program_results[0].site_name,
                admissions_projected=total_adm,
                los_effective=round(sum(r.los_effective for r in per_program_results) / len(per_program_results), 2),
                patient_days=total_days,
                census_average=round(total_days / 365.0, 1),
                required_beds=total_required,
                staffed_beds=total_staffed_for_site,
                capacity_gap=total_required - total_staffed_for_site,
                nursing_fte=round(site_total_fte, 1) if fte_count > 0 else None
            )

            site_results.append(aggregated)
            total_required_beds += aggregated.required_beds
            total_staffed_beds += aggregated.staffed_beds
            total_admissions += aggregated.admissions_projected
            total_patient_days += aggregated.patient_days
            if aggregated.nursing_fte:
                overall_total_fte = (overall_total_fte or 0) + aggregated.nursing_fte

        avg_occupancy = total_patient_days / (total_staffed_beds * 365) if total_staffed_beds > 0 else 0
        avg_los_effective = total_patient_days / total_admissions if total_admissions > 0 else 0

        kpis = ScenarioKPIs(
            total_required_beds=total_required_beds,
            total_staffed_beds=total_staffed_beds,
            total_capacity_gap=total_required_beds - total_staffed_beds,
            total_nursing_fte=overall_total_fte,
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

        # Extract parameters and coerce numeric types
        g = float(request.params.growth_pct)
        y = int(request.horizon_years)
        d = float(request.params.los_delta)
        occ_t = float(request.params.occupancy_target)
        alc_t = float(request.params.alc_target)
        alc_b = float(site_baseline.get('alc_rate', 0))
        los_b = float(site_baseline.get('los_base_days', 1.0))

        # Calculate projections
        admissions_projected = int(baseline_admissions * ((1 + g) ** y))
        los_acute = los_b * (1 + d)
        los_effective = los_acute * (1 + (alc_t - alc_b))

        # Apply bounds/guards
        los_effective = max(0.25, los_effective)

        # Get seasonality multiplier (using average of year)
        seasonality_factor = 1.0
        if request.params.seasonality:
            seasonality_factor = await self._get_average_seasonality(site_id, request.program_id)

        patient_days = int(admissions_projected * los_effective * seasonality_factor)
        census_average = patient_days / 365.0
        required_beds = math.ceil(census_average / occ_t) if occ_t > 0 else 0

        # Calculate nursing FTE if staffing factors available
        nursing_fte = None
        if staffing_factor:
            hppd = float(staffing_factor.get('hppd', 0))
            annual_hours = float(staffing_factor.get('annual_hours_per_fte', 1950))
            productivity = float(staffing_factor.get('productivity_factor', 1.0))

            total_hours_needed = required_beds * hppd * 365
            nursing_fte = round(total_hours_needed / (annual_hours * productivity), 1) if (annual_hours * productivity) > 0 else None

        return SiteResult(
            site_id=site_id,
            site_code=site_baseline.get('site_code', ''),
            site_name=site_baseline.get('site_name', ''),
            admissions_projected=admissions_projected,
            los_effective=round(los_effective, 2),
            patient_days=patient_days,
            census_average=round(census_average, 1),
            required_beds=required_beds,
            staffed_beds=site_beds.get('staffed_beds', 0),
            capacity_gap=required_beds - site_beds.get('staffed_beds', 0),
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
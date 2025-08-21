"""
Repository layer for database queries.
"""

from typing import List, Optional, Dict, Any
from .db import execute_query_dict
from .schemas import (
    Site, Program, Subprogram, StaffedBedsSchedule, 
    ClinicalBaseline, SeasonalityMonthly, StaffingFactor
)


class ReferenceRepository:
    """Repository for reference data queries."""
    
    @staticmethod
    async def get_sites() -> List[Dict[str, Any]]:
        """Get all sites."""
        query = """
            SELECT site_id, site_code, site_name 
            FROM dim_site 
            ORDER BY site_id
        """
        return await execute_query_dict(query)
    
    @staticmethod
    async def get_programs() -> List[Dict[str, Any]]:
        """Get all programs."""
        query = """
            SELECT program_id, program_name 
            FROM dim_program 
            ORDER BY program_id
        """
        return await execute_query_dict(query)
    
    @staticmethod
    async def get_subprograms(program_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get subprograms, optionally filtered by program."""
        query = """
            SELECT program_id, subprogram_id, subprogram_name 
            FROM dim_subprogram
        """
        params = []
        
        if program_id:
            query += " WHERE program_id = %s"
            params.append(program_id)
        
        query += " ORDER BY program_id, subprogram_id"
        return await execute_query_dict(query, params)
    
    @staticmethod
    async def get_staffed_beds(schedule_code: str = "Sched-A") -> List[Dict[str, Any]]:
        """Get staffed beds for a schedule."""
        query = """
            SELECT s.id, s.site_id, s.program_id, s.schedule_code, s.staffed_beds,
                   ds.site_code, ds.site_name, dp.program_name
            FROM staffed_beds_schedule s
            JOIN dim_site ds ON s.site_id = ds.site_id
            JOIN dim_program dp ON s.program_id = dp.program_id
            WHERE s.schedule_code = %s
            ORDER BY s.site_id, s.program_id
        """
        return await execute_query_dict(query, [schedule_code])
    
    @staticmethod
    async def get_clinical_baselines(year: int = 2022) -> List[Dict[str, Any]]:
        """Get clinical baselines for a year."""
        query = """
            SELECT c.id, c.site_id, c.program_id, c.baseline_year,
                   c.los_base_days, c.alc_rate,
                   ds.site_code, ds.site_name, dp.program_name
            FROM clinical_baseline c
            JOIN dim_site ds ON c.site_id = ds.site_id
            JOIN dim_program dp ON c.program_id = dp.program_id
            WHERE c.baseline_year = %s
            ORDER BY c.site_id, c.program_id
        """
        return await execute_query_dict(query, [year])
    
    @staticmethod
    async def get_seasonality(year: int = 2022) -> List[Dict[str, Any]]:
        """Get seasonality multipliers."""
        query = """
            SELECT id, site_id, program_id, month, multiplier
            FROM seasonality_monthly
            ORDER BY COALESCE(site_id, -1), COALESCE(program_id, -1), month
        """
        return await execute_query_dict(query)
    
    @staticmethod
    async def get_staffing_factors() -> List[Dict[str, Any]]:
        """Get staffing factors."""
        query = """
            SELECT sf.id, sf.program_id, sf.subprogram_id, sf.hppd,
                   sf.annual_hours_per_fte, sf.productivity_factor,
                   dp.program_name
            FROM staffing_factors sf
            JOIN dim_program dp ON sf.program_id = dp.program_id
            ORDER BY sf.program_id, sf.subprogram_id
        """
        return await execute_query_dict(query)


class ScenarioRepository:
    """Repository for scenario calculation data."""
    
    @staticmethod
    async def get_baseline_admissions(
        site_ids: List[int], 
        program_id: int, 
        baseline_year: int
    ) -> List[Dict[str, Any]]:
        """Get baseline admissions from historical data."""
        site_ids_str = ','.join(map(str, site_ids))
        
        query = f"""
            SELECT 
                ip.facility_id as site_id,
                COUNT(*) as admissions_base,
                AVG(ip.los_days) as los_observed,
                AVG(CASE WHEN ip.alc_flag=1 THEN 1 ELSE 0 END) as alc_rate_observed
            FROM ip_stays ip
            WHERE ip.facility_id IN ({site_ids_str})
              AND ip.program_id = %s
              AND YEAR(ip.admit_ts) = %s
            GROUP BY ip.facility_id
            ORDER BY ip.facility_id
        """
        return await execute_query_dict(query, [program_id, baseline_year])
    
    @staticmethod
    async def get_site_program_baseline(
        site_ids: List[int],
        program_id: int,
        baseline_year: int
    ) -> List[Dict[str, Any]]:
        """Get baseline clinical parameters for sites and program."""
        site_ids_str = ','.join(map(str, site_ids))
        
        query = f"""
            SELECT 
                c.site_id, c.program_id, c.baseline_year,
                c.los_base_days, c.alc_rate,
                ds.site_code, ds.site_name
            FROM clinical_baseline c
            JOIN dim_site ds ON c.site_id = ds.site_id
            WHERE c.site_id IN ({site_ids_str})
              AND c.program_id = %s
              AND c.baseline_year = %s
            ORDER BY c.site_id
        """
        return await execute_query_dict(query, [program_id, baseline_year])
    
    @staticmethod
    async def get_site_staffed_beds(
        site_ids: List[int],
        program_id: int,
        schedule_code: str = "Sched-A"
    ) -> List[Dict[str, Any]]:
        """Get staffed beds for sites and program."""
        site_ids_str = ','.join(map(str, site_ids))
        
        query = f"""
            SELECT s.site_id, s.program_id, s.staffed_beds,
                   ds.site_code, ds.site_name
            FROM staffed_beds_schedule s
            JOIN dim_site ds ON s.site_id = ds.site_id
            WHERE s.site_id IN ({site_ids_str})
              AND s.program_id = %s
              AND s.schedule_code = %s
            ORDER BY s.site_id
        """
        return await execute_query_dict(query, [program_id, schedule_code])
    
    @staticmethod
    async def get_staffing_factor(program_id: int) -> Optional[Dict[str, Any]]:
        """Get staffing factors for a program."""
        query = """
            SELECT hppd, annual_hours_per_fte, productivity_factor
            FROM staffing_factors
            WHERE program_id = %s AND subprogram_id IS NULL
            LIMIT 1
        """
        results = await execute_query_dict(query, [program_id])
        return results[0] if results else None
    
    @staticmethod
    async def get_seasonality_multiplier(
        site_id: Optional[int] = None,
        program_id: Optional[int] = None,
        month: int = 1
    ) -> float:
        """Get seasonality multiplier for specific site/program/month."""
        # Try specific site/program first
        if site_id and program_id:
            query = """
                SELECT multiplier FROM seasonality_monthly
                WHERE site_id = %s AND program_id = %s AND month = %s
                LIMIT 1
            """
            results = await execute_query_dict(query, [site_id, program_id, month])
            if results:
                return float(results[0]['multiplier'])
        
        # Try program-specific
        if program_id:
            query = """
                SELECT multiplier FROM seasonality_monthly
                WHERE site_id IS NULL AND program_id = %s AND month = %s
                LIMIT 1
            """
            results = await execute_query_dict(query, [program_id, month])
            if results:
                return float(results[0]['multiplier'])
        
        # Fall back to global
        query = """
            SELECT multiplier FROM seasonality_monthly
            WHERE site_id IS NULL AND program_id IS NULL AND month = %s
            LIMIT 1
        """
        results = await execute_query_dict(query, [month])
        return float(results[0]['multiplier']) if results else 1.0
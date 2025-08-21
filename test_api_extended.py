#!/usr/bin/env python3
"""
Extended API test with CSV fallback (no MySQL required).
Tests the new API endpoints using CSV data.
"""

import subprocess
import sys
import time
import json
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, Any


def setup_test_environment():
    """Set up test environment with necessary data."""
    print("Setting up test environment...")
    
    # Ensure basic data exists
    result = subprocess.run(['python', 'generate_data.py'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Basic data generation failed: {result.stderr}")
        return False
        
    # Generate reference data
    result = subprocess.run(['python', 'generate_refs.py'],
                          capture_output=True, text=True)  
    if result.returncode != 0:
        print(f"❌ Reference data generation failed: {result.stderr}")
        return False
    
    print("✓ Test environment ready")
    return True


def create_csv_repository_mock():
    """Create a mock repository that reads from CSV files."""
    
    csv_repo_code = '''
"""
CSV-based repository implementation for testing.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional


class CSVReferenceRepository:
    """Repository that reads from CSV files instead of MySQL."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    async def get_sites(self) -> List[Dict[str, Any]]:
        """Get all sites from CSV."""
        df = pd.read_csv(self.data_dir / "dim_site.csv")
        # Add site_id (auto-increment simulation)
        df['site_id'] = range(1, len(df) + 1)
        return df.to_dict('records')
    
    async def get_programs(self) -> List[Dict[str, Any]]:
        """Get all programs from CSV."""
        df = pd.read_csv(self.data_dir / "dim_program.csv")
        return df.to_dict('records')
    
    async def get_subprograms(self, program_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get subprograms from CSV."""
        df = pd.read_csv(self.data_dir / "dim_subprogram.csv")
        if program_id:
            df = df[df['program_id'] == program_id]
        return df.to_dict('records')
    
    async def get_staffed_beds(self, schedule_code: str = "Sched-A") -> List[Dict[str, Any]]:
        """Get staffed beds from CSV."""
        beds_df = pd.read_csv(self.data_dir / "staffed_beds_schedule.csv")
        sites_df = pd.read_csv(self.data_dir / "dim_site.csv")
        programs_df = pd.read_csv(self.data_dir / "dim_program.csv")
        
        # Add site_id to sites_df
        sites_df['site_id'] = range(1, len(sites_df) + 1)
        
        # Filter by schedule
        beds_df = beds_df[beds_df['schedule_code'] == schedule_code]
        
        # Join with dimension tables
        result = beds_df.merge(sites_df[['site_id', 'site_code', 'site_name']], on='site_id')
        result = result.merge(programs_df[['program_id', 'program_name']], on='program_id')
        
        return result.to_dict('records')
    
    async def get_clinical_baselines(self, year: int = 2022) -> List[Dict[str, Any]]:
        """Get clinical baselines from CSV."""
        baselines_df = pd.read_csv(self.data_dir / "clinical_baseline.csv")
        sites_df = pd.read_csv(self.data_dir / "dim_site.csv")
        programs_df = pd.read_csv(self.data_dir / "dim_program.csv")
        
        # Add site_id to sites_df
        sites_df['site_id'] = range(1, len(sites_df) + 1)
        
        # Filter by year
        baselines_df = baselines_df[baselines_df['baseline_year'] == year]
        
        # Join with dimension tables
        result = baselines_df.merge(sites_df[['site_id', 'site_code', 'site_name']], on='site_id')
        result = result.merge(programs_df[['program_id', 'program_name']], on='program_id')
        
        return result.to_dict('records')
    
    async def get_seasonality(self, year: int = 2022) -> List[Dict[str, Any]]:
        """Get seasonality from CSV."""
        df = pd.read_csv(self.data_dir / "seasonality_monthly.csv")
        # Add auto-increment id
        df['id'] = range(1, len(df) + 1)
        return df.to_dict('records')
    
    async def get_staffing_factors(self) -> List[Dict[str, Any]]:
        """Get staffing factors from CSV."""
        factors_df = pd.read_csv(self.data_dir / "staffing_factors.csv")
        programs_df = pd.read_csv(self.data_dir / "dim_program.csv")
        
        # Add auto-increment id
        factors_df['id'] = range(1, len(factors_df) + 1)
        
        # Join with programs
        result = factors_df.merge(programs_df[['program_id', 'program_name']], on='program_id')
        
        return result.to_dict('records')


class CSVScenarioRepository:
    """CSV-based scenario repository for testing."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    async def get_baseline_admissions(
        self, site_ids: List[int], program_id: int, baseline_year: int
    ) -> List[Dict[str, Any]]:
        """Get baseline admissions from IP stays CSV."""
        ip_df = pd.read_csv(self.data_dir / "ip_stays.csv")
        
        # Convert admit_ts to datetime and extract year
        ip_df['admit_ts'] = pd.to_datetime(ip_df['admit_ts'])
        ip_df['admit_year'] = ip_df['admit_ts'].dt.year
        
        # Filter by parameters
        filtered = ip_df[
            (ip_df['facility_id'].isin(site_ids)) &
            (ip_df['program_id'] == program_id) &
            (ip_df['admit_year'] == baseline_year)
        ]
        
        if filtered.empty:
            # Return dummy data if no historical data
            return [
                {
                    'site_id': site_id,
                    'admissions_base': 100,
                    'los_observed': 5.5,
                    'alc_rate_observed': 0.12
                }
                for site_id in site_ids
            ]
        
        # Group by site and calculate metrics
        grouped = filtered.groupby('facility_id').agg({
            'stay_id': 'count',
            'los_days': 'mean',
            'alc_flag': 'mean'
        }).reset_index()
        
        grouped.columns = ['site_id', 'admissions_base', 'los_observed', 'alc_rate_observed']
        
        return grouped.to_dict('records')
    
    async def get_site_program_baseline(
        self, site_ids: List[int], program_id: int, baseline_year: int
    ) -> List[Dict[str, Any]]:
        """Get baseline clinical parameters."""
        baselines_df = pd.read_csv(self.data_dir / "clinical_baseline.csv")
        sites_df = pd.read_csv(self.data_dir / "dim_site.csv")
        
        # Add site_id to sites_df
        sites_df['site_id'] = range(1, len(sites_df) + 1)
        
        # Filter by parameters
        filtered = baselines_df[
            (baselines_df['site_id'].isin(site_ids)) &
            (baselines_df['program_id'] == program_id) &
            (baselines_df['baseline_year'] == baseline_year)
        ]
        
        # Join with sites
        result = filtered.merge(sites_df[['site_id', 'site_code', 'site_name']], on='site_id')
        
        return result.to_dict('records')
    
    async def get_site_staffed_beds(
        self, site_ids: List[int], program_id: int, schedule_code: str = "Sched-A"
    ) -> List[Dict[str, Any]]:
        """Get staffed beds for sites."""
        beds_df = pd.read_csv(self.data_dir / "staffed_beds_schedule.csv")
        sites_df = pd.read_csv(self.data_dir / "dim_site.csv")
        
        # Add site_id to sites_df
        sites_df['site_id'] = range(1, len(sites_df) + 1)
        
        # Filter by parameters
        filtered = beds_df[
            (beds_df['site_id'].isin(site_ids)) &
            (beds_df['program_id'] == program_id) &
            (beds_df['schedule_code'] == schedule_code)
        ]
        
        # Join with sites
        result = filtered.merge(sites_df[['site_id', 'site_code', 'site_name']], on='site_id')
        
        return result.to_dict('records')
    
    async def get_staffing_factor(self, program_id: int) -> Optional[Dict[str, Any]]:
        """Get staffing factors for a program."""
        df = pd.read_csv(self.data_dir / "staffing_factors.csv")
        
        filtered = df[
            (df['program_id'] == program_id) &
            (df['subprogram_id'].isna())
        ]
        
        if not filtered.empty:
            return filtered.iloc[0].to_dict()
        return None
    
    async def get_seasonality_multiplier(
        self, site_id: Optional[int] = None, program_id: Optional[int] = None, month: int = 1
    ) -> float:
        """Get seasonality multiplier."""
        df = pd.read_csv(self.data_dir / "seasonality_monthly.csv")
        
        # Try specific site/program first
        if site_id and program_id:
            filtered = df[
                (df['site_id'] == site_id) &
                (df['program_id'] == program_id) &
                (df['month'] == month)
            ]
            if not filtered.empty:
                return float(filtered.iloc[0]['multiplier'])
        
        # Try program-specific
        if program_id:
            filtered = df[
                (df['site_id'].isna()) &
                (df['program_id'] == program_id) &
                (df['month'] == month)
            ]
            if not filtered.empty:
                return float(filtered.iloc[0]['multiplier'])
        
        # Fall back to global
        filtered = df[
            (df['site_id'].isna()) &
            (df['program_id'].isna()) &
            (df['month'] == month)
        ]
        
        if not filtered.empty:
            return float(filtered.iloc[0]['multiplier'])
        
        return 1.0
'''
    
    # Write the mock repository to a temporary file
    with open('csv_repositories.py', 'w') as f:
        f.write(csv_repo_code)


def test_scenario_calculation():
    """Test scenario calculation with CSV data."""
    print("Testing scenario calculation...")
    
    # Import the CSV repositories
    import csv_repositories
    from api.services import ScenarioService
    from api.schemas import ScenarioRequest, ScenarioParams
    
    # Monkey patch the repositories in the service
    service = ScenarioService()
    service.scenario_repo = csv_repositories.CSVScenarioRepository()
    service.ref_repo = csv_repositories.CSVReferenceRepository()
    
    # Create a test scenario request
    params = ScenarioParams(
        occupancy_target=0.90,
        los_delta=-0.03,
        alc_target=0.12,
        growth_pct=0.02,
        schedule_code="Sched-A",
        seasonality=False
    )
    
    request = ScenarioRequest(
        sites=[1, 2, 3],
        program_id=1,
        baseline_year=2022,
        horizon_years=3,
        params=params
    )
    
    try:
        # This should work without asyncio in a simple test
        import asyncio
        result = asyncio.run(service.calculate_scenario(request))
        
        # Validate result structure
        assert hasattr(result, 'kpis')
        assert hasattr(result, 'by_site')
        assert len(result.by_site) > 0
        assert result.kpis.total_required_beds > 0
        
        print(f"✓ Scenario calculation successful: {len(result.by_site)} sites processed")
        print(f"  Total required beds: {result.kpis.total_required_beds}")
        print(f"  Total capacity gap: {result.kpis.total_capacity_gap}")
        
        return True
    except Exception as e:
        print(f"❌ Scenario calculation failed: {e}")
        return False


def test_csv_repositories():
    """Test CSV repository functions."""
    print("Testing CSV repositories...")
    
    create_csv_repository_mock()
    import csv_repositories
    import asyncio
    
    try:
        ref_repo = csv_repositories.CSVReferenceRepository()
        
        # Test sites
        sites = asyncio.run(ref_repo.get_sites())
        assert len(sites) > 0
        assert 'site_id' in sites[0]
        assert 'site_code' in sites[0]
        
        # Test programs
        programs = asyncio.run(ref_repo.get_programs())
        assert len(programs) > 0
        assert 'program_id' in programs[0]
        
        # Test staffed beds
        beds = asyncio.run(ref_repo.get_staffed_beds("Sched-A"))
        assert len(beds) > 0
        assert 'staffed_beds' in beds[0]
        
        print("✓ CSV repositories working correctly")
        return True
    except Exception as e:
        print(f"❌ CSV repositories test failed: {e}")
        return False


def main():
    """Run all extended API tests."""
    print("🧪 Testing Extended API with CSV Data\n")
    
    # Setup
    if not setup_test_environment():
        return 1
    
    tests = [
        test_csv_repositories,
        test_scenario_calculation,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    # Cleanup
    csv_file = Path('csv_repositories.py')
    if csv_file.exists():
        csv_file.unlink()
    
    if passed == len(tests):
        print("🎉 All extended API tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
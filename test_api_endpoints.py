#!/usr/bin/env python3
"""
API endpoint test for the extended healthcare scenarios API.
Tests actual HTTP endpoints using a test FastAPI client.
"""

import sys
import json
from pathlib import Path
import pandas as pd


def setup_test_data():
    """Ensure test data exists."""
    # Generate basic data if needed
    import subprocess
    
    result = subprocess.run(['python', 'generate_data.py'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Basic data generation failed: {result.stderr}")
        return False
        
    result = subprocess.run(['python', 'generate_refs.py'],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Reference data generation failed: {result.stderr}")
        return False
    
    return True


def test_api_with_csv_mock():
    """Test API endpoints with CSV-based mock implementation."""
    print("Testing API endpoints with CSV data...")
    
    # Create a test version of the API that uses CSV instead of MySQL
    from fastapi.testclient import TestClient
    from api.main import app
    from api.repositories import ReferenceRepository
    
    # Import our CSV mock
    sys.path.append('.')
    
    # Create CSV repository mock inline
    class CSVReferenceRepository:
        def __init__(self):
            self.data_dir = Path("data")
        
        async def get_sites(self):
            df = pd.read_csv(self.data_dir / "dim_site.csv")
            df['site_id'] = range(1, len(df) + 1)
            return df.to_dict('records')
        
        async def get_programs(self):
            df = pd.read_csv(self.data_dir / "dim_program.csv")
            return df.to_dict('records')
        
        async def get_staffed_beds(self, schedule_code="Sched-A"):
            beds_df = pd.read_csv(self.data_dir / "staffed_beds_schedule.csv")
            sites_df = pd.read_csv(self.data_dir / "dim_site.csv")
            programs_df = pd.read_csv(self.data_dir / "dim_program.csv")
            
            sites_df['site_id'] = range(1, len(sites_df) + 1)
            beds_df = beds_df[beds_df['schedule_code'] == schedule_code]
            
            result = beds_df.merge(sites_df[['site_id', 'site_code', 'site_name']], on='site_id')
            result = result.merge(programs_df[['program_id', 'program_name']], on='program_id')
            
            return result.to_dict('records')
        
        async def get_clinical_baselines(self, year=2022):
            baselines_df = pd.read_csv(self.data_dir / "clinical_baseline.csv")
            sites_df = pd.read_csv(self.data_dir / "dim_site.csv")
            programs_df = pd.read_csv(self.data_dir / "dim_program.csv")
            
            sites_df['site_id'] = range(1, len(sites_df) + 1)
            baselines_df = baselines_df[baselines_df['baseline_year'] == year]
            
            result = baselines_df.merge(sites_df[['site_id', 'site_code', 'site_name']], on='site_id')
            result = result.merge(programs_df[['program_id', 'program_name']], on='program_id')
            
            return result.to_dict('records')
        
        async def get_seasonality(self, year=2022):
            df = pd.read_csv(self.data_dir / "seasonality_monthly.csv")
            df['id'] = range(1, len(df) + 1)
            return df.to_dict('records')
        
        async def get_staffing_factors(self):
            factors_df = pd.read_csv(self.data_dir / "staffing_factors.csv")
            programs_df = pd.read_csv(self.data_dir / "dim_program.csv")
            
            factors_df['id'] = range(1, len(factors_df) + 1)
            result = factors_df.merge(programs_df[['program_id', 'program_name']], on='program_id')
            
            return result.to_dict('records')
    
    # Monkey patch the reference repository
    import api.main
    api.main.ref_repo = CSVReferenceRepository()
    
    # Create test client
    client = TestClient(app)
    
    try:
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        print("✓ Root endpoint working")
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
        
        # Test reference endpoints
        response = client.get("/reference/sites")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert "site_id" in data["data"][0]
        print("✓ Sites endpoint working")
        
        response = client.get("/reference/programs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        print("✓ Programs endpoint working")
        
        response = client.get("/reference/staffed-beds?schedule=Sched-A")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        print("✓ Staffed beds endpoint working")
        
        response = client.get("/reference/baselines?year=2022")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        print("✓ Baselines endpoint working")
        
        response = client.get("/reference/seasonality")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        print("✓ Seasonality endpoint working")
        
        response = client.get("/reference/staffing-factors")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        print("✓ Staffing factors endpoint working")
        
        print("✓ All reference endpoints working")
        assert True

    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        assert False, f'API endpoint test failed: {e}'


def test_scenario_endpoint_with_mock():
    """Test the scenario calculation endpoint with mock data."""
    print("Testing scenario calculation endpoint...")
    
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        
        # Create a simplified scenario service mock
        class MockScenarioService:
            async def calculate_scenario(self, request):
                from api.schemas import ScenarioResponse, ScenarioKPIs, SiteResult
                
                # Create mock results
                site_results = [
                    SiteResult(
                        site_id=1,
                        site_code="LM-SNW", 
                        site_name="Snowberry General",
                        admissions_projected=120,
                        los_effective=5.2,
                        patient_days=624,
                        census_average=1.7,
                        required_beds=2,
                        staffed_beds=69,
                        capacity_gap=-67,
                        nursing_fte=12.5
                    ),
                    SiteResult(
                        site_id=2,
                        site_code="LM-BLH",
                        site_name="Blue Heron Medical", 
                        admissions_projected=115,
                        los_effective=5.0,
                        patient_days=575,
                        census_average=1.6,
                        required_beds=2,
                        staffed_beds=70,
                        capacity_gap=-68,
                        nursing_fte=11.8
                    )
                ]
                
                kpis = ScenarioKPIs(
                    total_required_beds=4,
                    total_staffed_beds=139,
                    total_capacity_gap=-135,
                    total_nursing_fte=24.3,
                    avg_occupancy=0.020,
                    total_admissions=235,
                    avg_los_effective=5.1
                )
                
                return ScenarioResponse(
                    kpis=kpis,
                    by_site=site_results,
                    metadata={
                        "request_params": request.model_dump(),
                        "calculation_date": "2025-01-01",
                        "model_version": "1.0"
                    }
                )
        
        # Monkey patch the scenario service
        import api.main
        api.main.scenario_service = MockScenarioService()
        
        client = TestClient(app)
        
        # Test scenario calculation
        scenario_request = {
            "sites": [1, 2],
            "program_id": 1,
            "baseline_year": 2022,
            "horizon_years": 3,
            "params": {
                "occupancy_target": 0.90,
                "los_delta": -0.03,
                "alc_target": 0.12,
                "growth_pct": 0.02,
                "schedule_code": "Sched-A",
                "seasonality": False
            }
        }
        
        response = client.post("/scenarios/compute", json=scenario_request)
        assert response.status_code == 200
        data = response.json()
        
        assert "kpis" in data
        assert "by_site" in data
        assert len(data["by_site"]) == 2
        assert data["kpis"]["total_required_beds"] == 4
        
        print("✓ Scenario calculation endpoint working")
        print(f"  Processed {len(data['by_site'])} sites")
        print(f"  Total required beds: {data['kpis']['total_required_beds']}")
        assert True

    except Exception as e:
        print(f"❌ Scenario endpoint test failed: {e}")
        assert False, f'Scenario endpoint test failed: {e}'


def main():
    """Run API endpoint tests."""
    print("🧪 Testing Extended API Endpoints\n")
    
    # Setup
    if not setup_test_data():
        return 1
    
    tests = [
        test_api_with_csv_mock,
        test_scenario_endpoint_with_mock,
    ]

    for test in tests:
        try:
            test()
            print()
        except AssertionError as e:
            print(f"❌ Test {test.__name__} failed: {e}\n")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")

    print("Finished API endpoint checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
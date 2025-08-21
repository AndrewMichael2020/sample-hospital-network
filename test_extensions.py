#!/usr/bin/env python3
"""
Test script for the new extended API functionality.
Tests the new reference data generation and API structure.
"""

import subprocess
import sys
import time
import json
import requests
from pathlib import Path


def test_reference_generation():
    """Test reference data generation."""
    print("Testing reference data generation...")
    
    # First ensure basic data exists
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
    
    # Check that files were created
    data_dir = Path('data')
    expected_files = [
        'staffed_beds_schedule.csv',
        'clinical_baseline.csv', 
        'seasonality_monthly.csv',
        'staffing_factors.csv'
    ]
    
    for file_name in expected_files:
        file_path = data_dir / file_name
        if not file_path.exists():
            print(f"❌ Missing expected file: {file_name}")
            return False
        
        # Check file has content
        with open(file_path) as f:
            lines = f.readlines()
            if len(lines) < 2:  # Header + at least one data row
                print(f"❌ File {file_name} appears empty or has no data")
                return False
    
    print("✓ Reference data generation successful")
    return True


def test_api_import():
    """Test that the new API modules can be imported."""
    print("Testing API module imports...")
    
    try:
        from api.config import settings
        from api.schemas import ScenarioRequest, ScenarioResponse
        from api.repositories import ReferenceRepository
        from api.services import ScenarioService
        print("✓ API modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ API module import failed: {e}")
        return False


def test_schema_validation():
    """Test Pydantic schema validation."""
    print("Testing schema validation...")
    
    try:
        from api.schemas import ScenarioRequest, ScenarioParams
        
        # Test valid request
        params = ScenarioParams(
            occupancy_target=0.90,
            los_delta=-0.03,
            alc_target=0.12,
            growth_pct=0.02
        )
        
        request = ScenarioRequest(
            sites=[1, 2, 3],
            program_id=1,
            baseline_year=2022,
            horizon_years=3,
            params=params
        )
        
        print("✓ Schema validation successful")
        return True
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False


def test_data_structure():
    """Test the structure of generated reference data."""
    print("Testing reference data structure...")
    
    import pandas as pd
    
    try:
        # Test staffed beds schedule
        df = pd.read_csv('data/staffed_beds_schedule.csv')
        expected_cols = ['site_id', 'program_id', 'schedule_code', 'staffed_beds']
        if not all(col in df.columns for col in expected_cols):
            print(f"❌ staffed_beds_schedule.csv missing expected columns")
            return False
        
        # Test clinical baseline  
        df = pd.read_csv('data/clinical_baseline.csv')
        expected_cols = ['site_id', 'program_id', 'baseline_year', 'los_base_days', 'alc_rate']
        if not all(col in df.columns for col in expected_cols):
            print(f"❌ clinical_baseline.csv missing expected columns")
            return False
        
        # Test seasonality
        df = pd.read_csv('data/seasonality_monthly.csv') 
        expected_cols = ['site_id', 'program_id', 'month', 'multiplier']
        if not all(col in df.columns for col in expected_cols):
            print(f"❌ seasonality_monthly.csv missing expected columns")
            return False
        
        # Check month range
        months = df['month'].unique()
        if not all(m in range(1, 13) for m in months):
            print(f"❌ seasonality months out of expected range")
            return False
        
        # Test staffing factors
        df = pd.read_csv('data/staffing_factors.csv')
        expected_cols = ['program_id', 'subprogram_id', 'hppd', 'annual_hours_per_fte', 'productivity_factor']
        if not all(col in df.columns for col in expected_cols):
            print(f"❌ staffing_factors.csv missing expected columns")
            return False
        
        print("✓ Data structure validation successful")
        return True
    except Exception as e:
        print(f"❌ Data structure validation failed: {e}")
        return False


def test_make_targets():
    """Test new make targets."""
    print("Testing new make targets...")
    
    # Test generate-refs target
    result = subprocess.run(['make', 'generate-refs'],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ make generate-refs failed: {result.stderr}")
        return False
    
    print("✓ Make targets successful")
    return True


def main():
    """Run all tests."""
    print("🧪 Testing Extended API Functionality\n")
    
    tests = [
        test_reference_generation,
        test_api_import,
        test_schema_validation,
        test_data_structure,
        test_make_targets,
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
    
    if passed == len(tests):
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
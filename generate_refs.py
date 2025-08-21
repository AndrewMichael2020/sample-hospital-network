#!/usr/bin/env python3
"""
Generate reference data for new extension tables.
Creates CSV files for staffed_beds_schedule, clinical_baseline, 
seasonality_monthly, and staffing_factors.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


def ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def generate_staffed_beds_schedule():
    """Generate staffed beds schedule data."""
    
    # Load existing sites and programs to ensure referential integrity
    sites_df = pd.read_csv("data/dim_site.csv")
    programs_df = pd.read_csv("data/dim_program.csv")
    
    records = []
    schedule_code = "Sched-A"
    
    # Generate staffed beds for key programs at each site
    key_programs = [1, 2, 4, 6]  # Medicine, Surgery, Critical Care, Emergency
    
    # Create site_id mapping since CSV doesn't include auto-increment IDs
    for idx, site in sites_df.iterrows():
        site_id = idx + 1  # Auto-increment starts at 1
        
        # Vary bed counts based on site (larger hospitals have more beds)
        base_medicine_beds = np.random.randint(40, 90)
        
        for program_id in key_programs:
            if program_id == 1:  # Medicine - largest allocation
                staffed_beds = base_medicine_beds
            elif program_id == 2:  # Surgery - about 30% of medicine
                staffed_beds = int(base_medicine_beds * 0.3)
            elif program_id == 4:  # Critical Care - about 15% of medicine
                staffed_beds = max(8, int(base_medicine_beds * 0.15))
            elif program_id == 6:  # Emergency - varies widely
                staffed_beds = np.random.randint(15, 35)
            
            records.append({
                'site_id': site_id,
                'program_id': program_id,
                'schedule_code': schedule_code,
                'staffed_beds': staffed_beds
            })
    
    df = pd.DataFrame(records)
    return df


def generate_clinical_baseline():
    """Generate clinical baseline data."""
    
    # Load existing sites and programs
    sites_df = pd.read_csv("data/dim_site.csv")
    programs_df = pd.read_csv("data/dim_program.csv")
    
    records = []
    baseline_year = 2022
    
    # LOS and ALC rates by program type
    program_baselines = {
        1: {'los_mean': 5.8, 'los_std': 0.8, 'alc_mean': 0.12, 'alc_std': 0.02},  # Medicine
        2: {'los_mean': 4.2, 'los_std': 0.4, 'alc_mean': 0.08, 'alc_std': 0.01},  # Surgery  
        3: {'los_mean': 6.5, 'los_std': 1.0, 'alc_mean': 0.15, 'alc_std': 0.03},  # MHSU
        4: {'los_mean': 8.3, 'los_std': 1.2, 'alc_mean': 0.05, 'alc_std': 0.02},  # Critical Care
        5: {'los_mean': 3.8, 'los_std': 0.5, 'alc_mean': 0.06, 'alc_std': 0.01},  # Periop
        6: {'los_mean': 0.5, 'los_std': 0.1, 'alc_mean': 0.02, 'alc_std': 0.01},  # Emergency
    }
    
    for idx, site in sites_df.iterrows():
        site_id = idx + 1  # Auto-increment starts at 1
        
        for program_id in program_baselines.keys():
            baseline = program_baselines[program_id]
            
            # Generate slightly varied values per site
            los_base = max(0.25, np.random.normal(baseline['los_mean'], baseline['los_std']))
            alc_rate = max(0.0, min(0.30, np.random.normal(baseline['alc_mean'], baseline['alc_std'])))
            
            records.append({
                'site_id': site_id,
                'program_id': program_id,
                'baseline_year': baseline_year,
                'los_base_days': round(los_base, 3),
                'alc_rate': round(alc_rate, 4)
            })
    
    df = pd.DataFrame(records)
    return df


def generate_seasonality_monthly():
    """Generate seasonality multipliers."""
    
    records = []
    
    # Global seasonality pattern (site_id=NULL, program_id=NULL)
    global_multipliers = {
        1: 1.00, 2: 1.00, 3: 1.02, 4: 1.01, 5: 1.00, 6: 1.00,
        7: 0.98, 8: 0.98, 9: 1.01, 10: 1.02, 11: 1.03, 12: 1.04
    }
    
    for month, multiplier in global_multipliers.items():
        records.append({
            'site_id': None,
            'program_id': None, 
            'month': month,
            'multiplier': multiplier
        })
    
    # Add some program-specific variations
    program_variations = {
        6: {7: 1.05, 8: 1.05, 12: 1.08, 1: 1.06}  # Emergency higher in summer/winter
    }
    
    for program_id, month_multipliers in program_variations.items():
        for month, multiplier in month_multipliers.items():
            records.append({
                'site_id': None,
                'program_id': program_id,
                'month': month, 
                'multiplier': multiplier
            })
    
    df = pd.DataFrame(records)
    return df


def generate_staffing_factors():
    """Generate staffing factors for FTE calculations."""
    
    records = []
    
    # Hours per patient day (HPPD) by program
    program_hppd = {
        1: 6.5,   # Medicine
        2: 5.8,   # Surgery  
        3: 8.2,   # MHSU
        4: 12.5,  # Critical Care
        5: 4.5,   # Periop
        6: 4.2,   # Emergency
    }
    
    for program_id, hppd in program_hppd.items():
        # Add some variation
        actual_hppd = hppd * np.random.uniform(0.95, 1.05)
        
        records.append({
            'program_id': program_id,
            'subprogram_id': None,
            'hppd': round(actual_hppd, 3),
            'annual_hours_per_fte': 1950,
            'productivity_factor': round(np.random.uniform(0.88, 0.95), 3)
        })
    
    df = pd.DataFrame(records)
    return df


def main():
    """Generate all reference data files."""
    print("Generating reference data...")
    
    data_dir = ensure_data_dir()
    
    # Generate each reference table
    print("Generating staffed beds schedule...")
    staffed_beds_df = generate_staffed_beds_schedule()
    staffed_beds_df.to_csv(data_dir / "staffed_beds_schedule.csv", index=False)
    print(f"Generated {len(staffed_beds_df)} staffed beds records")
    
    print("Generating clinical baselines...")
    clinical_df = generate_clinical_baseline()
    clinical_df.to_csv(data_dir / "clinical_baseline.csv", index=False)
    print(f"Generated {len(clinical_df)} clinical baseline records")
    
    print("Generating seasonality data...")
    seasonality_df = generate_seasonality_monthly()
    seasonality_df.to_csv(data_dir / "seasonality_monthly.csv", index=False)  
    print(f"Generated {len(seasonality_df)} seasonality records")
    
    print("Generating staffing factors...")
    staffing_df = generate_staffing_factors()
    staffing_df.to_csv(data_dir / "staffing_factors.csv", index=False)
    print(f"Generated {len(staffing_df)} staffing factor records")
    
    print("Reference data generation complete!")
    

if __name__ == "__main__":
    main()
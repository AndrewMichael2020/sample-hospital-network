#!/usr/bin/env python3
"""
Generate synthetic healthcare data for Lower Mainland hospital network.
Creates CSV files with fake data that matches the schema defined in schema.sql
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import uuid
import os

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

# Constants from copilot_instructions.md
FACILITIES = [
    ("LM-SNW", "Snowberry General"),
    ("LM-BLH", "Blue Heron Medical"),
    ("LM-SLM", "Salmon Run Hospital"),
    ("LM-MSC", "Mossy Cedar Community"),
    ("LM-OTB", "Otter Bay Medical Centre"),
    ("LM-BRC", "Bear Creek Hospital"),
    ("LM-DFT", "Driftwood Regional"),
    ("LM-STG", "Stargazer Health Centre"),
    ("LM-SRC", "Sunrise Coast Hospital"),
    ("LM-GRS", "Grouse Ridge Medical"),
    ("LM-FGH", "Foggy Harbor Hospital"),
    ("LM-GPK", "Granite Peak Medical")
]

LHAS_TO_FACILITIES = [
    ("Harborview", "LM-FGH"),
    ("Riverbend", "LM-BRC"),
    ("North Shoreline", "LM-GRS"),
    ("Cedar Heights", "LM-MSC"),
    ("Lakeside Plains", "LM-SNW"),
    ("Granite Hills", "LM-GPK"),
    ("Sunset Promenade", "LM-SRC"),
    ("Driftwood Inlet", "LM-DFT"),
    ("Otter Cove", "LM-OTB"),
    ("Blueberry Meadows", "LM-BLH"),
    ("Silver Falls", "LM-SLM"),
    ("Stargazer Valley", "LM-STG")
]

PROGRAMS = [
    (1, "Medicine"),
    (2, "Inpatient MHSU"),
    (3, "MICY"),
    (4, "Critical Care"),
    (5, "Surgery / Periop"),
    (6, "Emergency"),
    (7, "Cardiac"),
    (8, "Renal"),
    (9, "Rehabilitation"),
    (10, "Primary Health Care"),
    (11, "Chronic Disease Mgmt"),
    (12, "Population & Public Health"),
    (13, "Palliative Care"),
    (14, "Trauma"),
    (15, "Specialized Community Services"),
    (16, "Pain Services")
]

SUBPROGRAMS = [
    (1, 1, "General Medicine"),
    (1, 2, "Hospitalist"),
    (1, 3, "ACE (Acute Care for Elderly)"),
    (2, 1, "Adult Inpatient Psychiatry"),
    (2, 2, "Psychiatric High Acuity/ICU"),
    (2, 3, "Substance Use Stabilization"),
    (3, 1, "Labour & Delivery"),
    (3, 2, "Post-partum/Maternity"),
    (3, 3, "Inpatient Pediatrics"),
    (4, 1, "ICU (Med-Surg)"),
    (4, 2, "High Acuity/Step-Down"),
    (4, 3, "Rapid Response/Outreach"),
    (5, 1, "Operating Room"),
    (5, 2, "PACU/Day Surgery"),
    (5, 3, "Surgical Inpatient Unit"),
    (6, 1, "Adult ED"),
    (6, 2, "Pediatric ED"),
    (6, 3, "Urgent Care Centre")
]

AGE_GROUPS = ["0-4", "5-14", "15-24", "25-44", "45-64", "65-74", "75-84", "85+"]
GENDERS = ["Female", "Male", "Other"]
ED_SUBSERVICES = ["Adult ED", "Pediatric ED", "Urgent Care Centre"]

def create_output_dir():
    """Create output directory for CSV files"""
    os.makedirs("data", exist_ok=True)

def generate_dim_site():
    """Generate facility dimension data"""
    return pd.DataFrame(FACILITIES, columns=["site_code", "site_name"])

def generate_dim_program():
    """Generate program dimension data"""
    return pd.DataFrame(PROGRAMS, columns=["program_id", "program_name"])

def generate_dim_subprogram():
    """Generate subprogram dimension data"""
    # Only include first 3 subprograms for simplicity
    subprogs = [(pid, sid, name) for pid, sid, name in SUBPROGRAMS if pid <= 6]
    return pd.DataFrame(subprogs, columns=["program_id", "subprogram_id", "subprogram_name"])

def generate_dim_lha():
    """Generate local health area dimension data"""
    site_lookup = {code: idx + 1 for idx, (code, name) in enumerate(FACILITIES)}
    
    lha_data = []
    for idx, (lha_name, facility_code) in enumerate(LHAS_TO_FACILITIES):
        lha_data.append({
            "lha_name": lha_name,
            "default_site_id": site_lookup[facility_code]
        })
    
    return pd.DataFrame(lha_data)

def generate_population_projection():
    """Generate population projection data for 2025-2034"""
    data = []
    
    for year in range(2025, 2035):  # 10 years
        for lha_idx in range(1, 13):  # 12 LHAs
            for age_group in AGE_GROUPS:
                for gender in GENDERS:
                    # Base population with some variation by LHA and age group
                    base_pop = {
                        "0-4": 800,
                        "5-14": 1200,
                        "15-24": 1500,
                        "25-44": 2000,
                        "45-64": 1800,
                        "65-74": 1200,
                        "75-84": 800,
                        "85+": 400
                    }[age_group]
                    
                    # LHA size variation (some LHAs are larger)
                    lha_multiplier = 1.5 if lha_idx in [1, 3, 5] else 1.0
                    
                    # Gender distribution (roughly equal, with small "Other" population)
                    gender_multiplier = 0.49 if gender in ["Female", "Male"] else 0.02
                    
                    # Annual growth
                    growth_rate = 1 + (0.01 * (year - 2025))  # 1% per year
                    
                    population = int(base_pop * lha_multiplier * gender_multiplier * growth_rate)
                    
                    data.append({
                        "year": year,
                        "lha_id": lha_idx,
                        "age_group": age_group,
                        "gender": gender,
                        "population": population
                    })
    
    return pd.DataFrame(data)

def generate_ed_baseline_rates():
    """Generate ED baseline rates per 1000 population"""
    data = []
    
    for lha_idx in range(1, 13):  # 12 LHAs
        for age_group in AGE_GROUPS:
            for gender in GENDERS:
                for ed_subservice in ED_SUBSERVICES:
                    # Different rates by age group and service
                    if ed_subservice == "Pediatric ED":
                        if age_group in ["0-4", "5-14"]:
                            base_rate = random.uniform(150, 250)
                        elif age_group == "15-24":
                            base_rate = random.uniform(50, 100)
                        else:
                            base_rate = random.uniform(5, 20)
                    elif ed_subservice == "Adult ED":
                        if age_group in ["0-4", "5-14"]:
                            base_rate = random.uniform(10, 30)
                        elif age_group in ["75-84", "85+"]:
                            base_rate = random.uniform(200, 400)
                        else:
                            base_rate = random.uniform(80, 150)
                    else:  # Urgent Care Centre
                        base_rate = random.uniform(40, 80)
                    
                    # Small gender variation
                    if gender == "Female":
                        rate = base_rate * random.uniform(0.95, 1.05)
                    elif gender == "Male":
                        rate = base_rate * random.uniform(0.90, 1.10)
                    else:
                        rate = base_rate * random.uniform(0.85, 1.15)
                    
                    data.append({
                        "lha_id": lha_idx,
                        "age_group": age_group,
                        "gender": gender,
                        "ed_subservice": ed_subservice,
                        "baserate_per_1000": round(rate, 2)
                    })
    
    return pd.DataFrame(data)

def generate_patients(n_patients=1000):
    """Generate synthetic patient data"""
    data = []
    
    for i in range(n_patients):
        # Generate patient ID
        patient_id = f"P{str(uuid.uuid4()).replace('-', '')[:12].upper()}"
        
        # Random LHA and facility
        lha_id = random.randint(1, 12)
        
        # 90% of patients use their default facility, 10% cross-over
        if random.random() < 0.9:
            facility_home_id = lha_id  # Default mapping
        else:
            facility_home_id = random.randint(1, 12)
        
        # Age and gender
        age_group = random.choice(AGE_GROUPS)
        gender = random.choices(GENDERS, weights=[49, 49, 2])[0]
        
        # Generate DOB consistent with age group
        current_year = 2025
        if age_group == "0-4":
            age = random.randint(0, 4)
        elif age_group == "5-14":
            age = random.randint(5, 14)
        elif age_group == "15-24":
            age = random.randint(15, 24)
        elif age_group == "25-44":
            age = random.randint(25, 44)
        elif age_group == "45-64":
            age = random.randint(45, 64)
        elif age_group == "65-74":
            age = random.randint(65, 74)
        elif age_group == "75-84":
            age = random.randint(75, 84)
        else:  # 85+
            age = random.randint(85, 95)
        
        dob = datetime(current_year - age, random.randint(1, 12), random.randint(1, 28)).date()
        
        # Primary ED service (age-appropriate)
        if age < 18:
            primary_ed_subservice = "Pediatric ED"
        elif age >= 65:
            primary_ed_subservice = random.choices(["Adult ED", "Urgent Care Centre"], weights=[70, 30])[0]
        else:
            primary_ed_subservice = random.choices(["Adult ED", "Urgent Care Centre"], weights=[60, 40])[0]
        
        # Expected ED rate and visits
        expected_ed_rate = random.uniform(0.5, 3.0)
        ed_visits_year = max(1, int(np.random.poisson(expected_ed_rate)))
        
        data.append({
            "patient_id": patient_id,
            "lha_id": lha_id,
            "facility_home_id": facility_home_id,
            "age_group": age_group,
            "gender": gender,
            "dob": dob,
            "primary_ed_subservice": primary_ed_subservice,
            "expected_ed_rate": round(expected_ed_rate, 4),
            "ed_visits_year": ed_visits_year
        })
    
    return pd.DataFrame(data)

def generate_ed_encounters(patients_df, n_encounters_per_patient=2):
    """Generate ED encounters for patients"""
    data = []
    encounter_id = 1
    
    for _, patient in patients_df.iterrows():
        # Number of encounters for this patient
        n_encounters = min(patient["ed_visits_year"], n_encounters_per_patient)
        
        for _ in range(n_encounters):
            # Random timestamp in 2025
            arrival_ts = fake.date_time_between(
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31)
            )
            
            # 90% at home facility, 10% elsewhere
            if random.random() < 0.9:
                facility_id = patient["facility_home_id"]
            else:
                facility_id = random.randint(1, 12)
            
            # ED service
            ed_subservice = patient["primary_ed_subservice"]
            
            # Acuity (1=most urgent, 5=least urgent)
            acuity = random.choices([1, 2, 3, 4, 5], weights=[5, 15, 40, 30, 10])[0]
            
            # Disposition
            dispo = random.choices(
                ["Discharge", "Admit", "Transfer", "AMA", "Death"],
                weights=[75, 15, 5, 4, 1]
            )[0]
            
            data.append({
                "encounter_id": encounter_id,
                "patient_id": patient["patient_id"],
                "facility_id": facility_id,
                "ed_subservice": ed_subservice,
                "arrival_ts": arrival_ts,
                "acuity": acuity,
                "dispo": dispo
            })
            encounter_id += 1
    
    return pd.DataFrame(data)

def generate_ip_stays(patients_df, n_stays_per_patient=1):
    """Generate inpatient stays for some patients"""
    data = []
    stay_id = 1
    
    # Only 20% of patients have IP stays
    ip_patients = patients_df.sample(frac=0.2)
    
    for _, patient in ip_patients.iterrows():
        for _ in range(n_stays_per_patient):
            # Random admission in 2025
            admit_ts = fake.date_time_between(
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 11, 30)  # Leave time for discharge
            )
            
            # Facility (usually home facility)
            facility_id = patient["facility_home_id"]
            
            # Program and subprogram
            program_id = random.randint(1, 6)  # Only using first 6 programs
            subprogram_id = random.randint(1, 3)
            
            # Length of stay (varies by age and program)
            if patient["age_group"] in ["75-84", "85+"]:
                los_days = max(0.25, np.random.lognormal(mean=2.0, sigma=1.0))
            elif program_id == 4:  # Critical Care
                los_days = max(0.25, np.random.lognormal(mean=1.5, sigma=0.8))
            else:
                los_days = max(0.25, np.random.lognormal(mean=1.0, sigma=0.6))
            
            los_days = round(los_days, 2)
            
            # Discharge timestamp
            discharge_ts = admit_ts + timedelta(days=los_days)
            
            # ALC flag (higher for elderly and medicine)
            alc_prob = 0.1
            if patient["age_group"] in ["75-84", "85+"]:
                alc_prob = 0.3
            if program_id == 1:  # Medicine
                alc_prob *= 2
            
            alc_flag = 1 if random.random() < alc_prob else 0
            
            data.append({
                "stay_id": stay_id,
                "patient_id": patient["patient_id"],
                "facility_id": facility_id,
                "program_id": program_id,
                "subprogram_id": subprogram_id,
                "admit_ts": admit_ts,
                "discharge_ts": discharge_ts,
                "los_days": los_days,
                "alc_flag": alc_flag
            })
            stay_id += 1
    
    return pd.DataFrame(data)

def main():
    """Generate all sample data and save to CSV files"""
    print("Generating synthetic healthcare data...")
    create_output_dir()
    
    # Generate dimension tables
    print("Creating dimension tables...")
    dim_site = generate_dim_site()
    dim_program = generate_dim_program()
    dim_subprogram = generate_dim_subprogram()
    dim_lha = generate_dim_lha()
    
    # Generate reference tables
    print("Creating population and rates tables...")
    population_projection = generate_population_projection()
    ed_baseline_rates = generate_ed_baseline_rates()
    
    # Generate patient data
    print("Creating patient data...")
    patients = generate_patients(n_patients=1000)  # Start with 1000 patients
    
    # Generate encounter data
    print("Creating encounters...")
    ed_encounters = generate_ed_encounters(patients)
    ip_stays = generate_ip_stays(patients)
    
    # Save all data to CSV
    print("Saving data to CSV files...")
    dim_site.to_csv("data/dim_site.csv", index=False)
    dim_program.to_csv("data/dim_program.csv", index=False)
    dim_subprogram.to_csv("data/dim_subprogram.csv", index=False)
    dim_lha.to_csv("data/dim_lha.csv", index=False)
    population_projection.to_csv("data/population_projection.csv", index=False)
    ed_baseline_rates.to_csv("data/ed_baseline_rates.csv", index=False)
    patients.to_csv("data/patients.csv", index=False)
    ed_encounters.to_csv("data/ed_encounters.csv", index=False)
    ip_stays.to_csv("data/ip_stays.csv", index=False)
    
    print(f"Generated {len(dim_site)} facilities")
    print(f"Generated {len(dim_program)} programs")
    print(f"Generated {len(dim_subprogram)} subprograms")
    print(f"Generated {len(dim_lha)} LHAs")
    print(f"Generated {len(population_projection)} population records")
    print(f"Generated {len(ed_baseline_rates)} ED rate records")
    print(f"Generated {len(patients)} patients")
    print(f"Generated {len(ed_encounters)} ED encounters")
    print(f"Generated {len(ip_stays)} IP stays")
    print("Data generation complete!")

if __name__ == "__main__":
    main()
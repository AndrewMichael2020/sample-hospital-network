#!/usr/bin/env python3
"""
SDV custom constraints for healthcare data generation.
Implements business rules and data consistency constraints.
"""

from datetime import datetime, date
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Use the current SDV constraints API
try:
    from sdv.constraints.tabular import FixedCombinations, FixedIncrements, Inequality
    from sdv.constraints.base import Constraint
    SDV_AVAILABLE = True
except ImportError:
    SDV_AVAILABLE = False
    print("Warning: SDV constraints not available. Using placeholder implementations.")


def define_healthcare_constraints():
    """
    Define all custom constraints for the healthcare dataset.
    Returns a list of constraint objects for use in SDV model training.
    """
    if not SDV_AVAILABLE:
        return []
        
    constraints = []
    
    # Due to API changes in SDV, we'll skip complex constraints for now
    # and focus on post-processing validation and correction
    
    logger.info("Using post-processing approach for constraints due to SDV API changes")
    
    return constraints


def validate_age_consistency(data: pd.DataFrame, reference_date: date = None) -> pd.Series:
    """
    Validate DOB to age group consistency.
    Returns a boolean Series indicating which records are consistent.
    """
    if reference_date is None:
        reference_date = date(2025, 1, 1)
    
    def calculate_expected_age_group(dob):
        if pd.isna(dob):
            return None
        dob_date = pd.to_datetime(dob).date() if not isinstance(dob, date) else dob
        age = (reference_date - dob_date).days // 365
        
        if age < 15:
            return "0-14"
        elif age < 25:
            return "15-24"
        elif age < 45:
            return "25-44"
        elif age < 65:
            return "45-64"
        elif age < 75:
            return "65-74"
        elif age < 85:
            return "75-84"
        else:
            return "85+"
    
    if 'dob' not in data.columns or 'age_group' not in data.columns:
        return pd.Series([True] * len(data), index=data.index)
    
    expected_age_groups = data['dob'].apply(calculate_expected_age_group)
    return expected_age_groups == data['age_group']


def validate_los_minimum(data: pd.DataFrame, min_los: float = 0.25) -> pd.Series:
    """
    Validate LOS is at least the minimum required.
    Returns a boolean Series indicating which records meet the requirement.
    """
    if 'los_days' not in data.columns:
        return pd.Series([True] * len(data), index=data.index)
    
    return data['los_days'] >= min_los


def validate_timestamp_order(data: pd.DataFrame) -> pd.Series:
    """
    Validate that discharge timestamp is after admit timestamp.
    Returns a boolean Series indicating which records are valid.
    """
    if 'admit_ts' not in data.columns or 'discharge_ts' not in data.columns:
        return pd.Series([True] * len(data), index=data.index)
    
    admit_ts = pd.to_datetime(data['admit_ts'])
    discharge_ts = pd.to_datetime(data['discharge_ts'])
    
    return discharge_ts >= admit_ts


def validate_alc_los_relationship(data: pd.DataFrame, min_alc_los: float = 1.0) -> pd.Series:
    """
    Validate that ALC patients have reasonable LOS (typically >= 1 day).
    Returns a boolean Series indicating which records are valid.
    """
    if 'alc_flag' not in data.columns or 'los_days' not in data.columns:
        return pd.Series([True] * len(data), index=data.index)
    
    # Non-ALC patients are always valid for this check
    result = pd.Series([True] * len(data), index=data.index)
    
    # ALC patients should have LOS >= min_alc_los
    alc_mask = data['alc_flag'] == 1
    result[alc_mask] = data.loc[alc_mask, 'los_days'] >= min_alc_los
    
    return result


def validate_pediatric_ed_rules(patients_data: pd.DataFrame, ed_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate pediatric ED business rules.
    Returns validation results with pass/fail status and details.
    """
    if 'patient_id' not in patients_data.columns or 'age_group' not in patients_data.columns:
        return {'pass': False, 'error': 'Missing required patient columns'}
    
    if 'patient_id' not in ed_data.columns or 'ed_subservice' not in ed_data.columns:
        return {'pass': False, 'error': 'Missing required ED columns'}
    
    # Join ED encounters with patient age groups
    ed_with_age = ed_data.merge(
        patients_data[['patient_id', 'age_group']], 
        on='patient_id'
    )
    
    results = {'pass': True, 'details': {}}
    
    # Rule 1: Pediatric ED should primarily serve young patients
    pediatric_ed_encounters = ed_with_age[ed_with_age['ed_subservice'] == 'Pediatric ED']
    if len(pediatric_ed_encounters) > 0:
        young_in_pediatric = pediatric_ed_encounters['age_group'].isin(['0-14', '15-24']).sum()
        pediatric_young_share = young_in_pediatric / len(pediatric_ed_encounters)
        
        pediatric_pass = pediatric_young_share >= 0.7  # 70% threshold
        results['details']['pediatric_young_share'] = {
            'share': pediatric_young_share,
            'threshold': 0.7,
            'pass': pediatric_pass
        }
        
        if not pediatric_pass:
            results['pass'] = False
    
    # Rule 2: Adult patients should rarely use Pediatric ED
    adult_age_groups = ['25-44', '45-64', '65-74', '75-84', '85+']
    adult_encounters = ed_with_age[ed_with_age['age_group'].isin(adult_age_groups)]
    
    if len(adult_encounters) > 0:
        pediatric_in_adults = adult_encounters['ed_subservice'].eq('Pediatric ED').sum()
        pediatric_adult_share = pediatric_in_adults / len(adult_encounters)
        
        adult_pass = pediatric_adult_share <= 0.1  # 10% threshold
        results['details']['pediatric_adult_share'] = {
            'share': pediatric_adult_share,
            'threshold': 0.1,
            'pass': adult_pass
        }
        
        if not adult_pass:
            results['pass'] = False
    
    return results


def apply_data_corrections(data: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """
    Apply corrections to ensure data meets business constraints.
    This is used as a post-processing step for synthetic data.
    """
    corrected_data = data.copy()
    
    if table_name == 'patients':
        # Ensure age group consistency with DOB
        reference_date = date(2025, 1, 1)
        
        def calculate_age_group(dob):
            if pd.isna(dob):
                return None
            # Handle both pandas Timestamp and date objects
            if isinstance(dob, pd.Timestamp):
                dob_date = dob.date()
            elif hasattr(dob, 'date'):
                dob_date = dob.date()
            else:
                dob_date = pd.to_datetime(dob).date()
            
            age = (reference_date - dob_date).days // 365
            
            if age < 15:
                return "0-14"
            elif age < 25:
                return "15-24"
            elif age < 45:
                return "25-44"
            elif age < 65:
                return "45-64"
            elif age < 75:
                return "65-74"
            elif age < 85:
                return "75-84"
            else:
                return "85+"
        
        if 'dob' in corrected_data.columns:
            corrected_data['age_group'] = corrected_data['dob'].apply(calculate_age_group)
    
    elif table_name == 'ip_stays':
        # Ensure LOS >= 0.25 days
        if 'los_days' in corrected_data.columns:
            corrected_data['los_days'] = np.maximum(corrected_data['los_days'], 0.25)
        
        # Ensure discharge is after admit
        if 'admit_ts' in corrected_data.columns and 'discharge_ts' in corrected_data.columns:
            admit_ts = pd.to_datetime(corrected_data['admit_ts'])
            discharge_ts = pd.to_datetime(corrected_data['discharge_ts'])
            
            # Fix cases where discharge is before admit
            invalid_mask = discharge_ts < admit_ts
            corrected_data.loc[invalid_mask, 'discharge_ts'] = (
                admit_ts[invalid_mask] + pd.Timedelta(hours=1)
            )
        
        # Ensure ALC patients have reasonable LOS
        if 'alc_flag' in corrected_data.columns and 'los_days' in corrected_data.columns:
            alc_mask = corrected_data['alc_flag'] == 1
            corrected_data.loc[alc_mask, 'los_days'] = np.maximum(
                corrected_data.loc[alc_mask, 'los_days'], 1.0
            )
    
    elif table_name == 'ed_encounters':
        # Apply pediatric ED corrections if patient data is available
        # This would require joining with patient data, so skip for now
        pass
    
    return corrected_data


def get_categorical_constraints() -> Dict[str, List]:
    """
    Define valid categorical values for enum fields.
    Returns dict of field -> valid_values mappings.
    """
    return {
        'gender': ['Female', 'Male', 'Other'],
        'age_group': ['0-14', '15-24', '25-44', '45-64', '65-74', '75-84', '85+'],
        'ed_subservice': ['Adult ED', 'Pediatric ED', 'Urgent Care Centre'],
        'dispo': ['Discharge', 'Transfer', 'AMA', 'Admit'],
        'acuity': [1, 2, 3, 4, 5],
        'alc_flag': [0, 1],
        # Facility IDs (1-12 based on schema)
        'facility_id': list(range(1, 13)),
        'facility_home_id': list(range(1, 13)),
        # LHA IDs (1-12 based on schema)
        'lha_id': list(range(1, 13)),
        # Program IDs (1-16 based on schema)
        'program_id': list(range(1, 17)),
        # Subprogram IDs (1-3 for each program)
        'subprogram_id': [1, 2, 3]
    }


def get_valid_program_subprogram_combinations() -> List[tuple]:
    """
    Get valid program/subprogram combinations based on the schema.
    Returns list of (program_id, subprogram_id) tuples.
    """
    # Based on generate_data.py SUBPROGRAMS definition
    # Each program has subprograms 1, 2, 3
    combinations = []
    for program_id in range(1, 17):  # Programs 1-16
        for subprogram_id in [1, 2, 3]:
            combinations.append((program_id, subprogram_id))
    
    return combinations
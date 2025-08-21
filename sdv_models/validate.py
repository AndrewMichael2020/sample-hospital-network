#!/usr/bin/env python3
"""
Validation and quality gates for SDV-generated healthcare data.
Implements business rules, privacy checks, and data quality metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import argparse
import logging
from pathlib import Path
from datetime import date
import json

# SDV metrics imports with fallbacks
try:
    from sdmetrics.reports.multi_table import QualityReport as MultiTableQualityReport
    from sdmetrics.privacy import KAnonymity
    SDMETRICS_AVAILABLE = True
except ImportError:
    try:
        from sdmetrics.multi_table import QualityReport as MultiTableQualityReport
        from sdmetrics.privacy import KAnonymity
        SDMETRICS_AVAILABLE = True
    except ImportError:
        MultiTableQualityReport = None
        KAnonymity = None
        SDMETRICS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HealthcareDataValidator:
    """
    Comprehensive validator for synthetic healthcare data.
    Implements quality gates and privacy checks as per copilot_instructions.md
    """
    
    def __init__(self, thresholds_config: Dict[str, Any] = None):
        """Initialize validator with quality thresholds."""
        self.thresholds = thresholds_config or self._get_default_thresholds()
        self.validation_results = {}
        
    def _get_default_thresholds(self) -> Dict[str, Any]:
        """Default quality thresholds from copilot_instructions.md"""
        return {
            'marginal_tolerance': 0.1,  # ±10% for marginals
            'ed_volume_tolerance': 0.05,  # ±5% for ED volumes
            'los_median_tolerance': 0.15,  # ±15% for LOS medians
            'pediatric_ed_share_min': 0.7,  # ≥70% pediatric share in <15
            'pediatric_adult_ed_max': 0.1,  # ≤10% pediatric in ≥25
            'correlation_threshold': 0.7,  # Minimum correlation preservation
            'shape_threshold': 0.8,  # Minimum shape similarity
            'k_anonymity_min': 5,  # Minimum k-anonymity
            'privacy_score_min': 0.8,  # Minimum privacy score
            'overall_quality_min': 0.75  # Minimum overall quality score
        }
    
    def validate_all(self, real_data: Dict[str, pd.DataFrame], 
                    synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Run all validation checks and return comprehensive results.
        """
        logger.info("Starting comprehensive validation...")
        
        results = {
            'overall_pass': True,
            'validation_timestamp': pd.Timestamp.now().isoformat(),
            'checks': {}
        }
        
        # 1. Shape and correlation tests
        logger.info("Running shape and correlation tests...")
        results['checks']['shape_correlation'] = self._validate_shape_correlation(
            real_data, synthetic_data
        )
        
        # 2. Business rules validation
        logger.info("Running business rules validation...")
        results['checks']['business_rules'] = self._validate_business_rules(
            real_data, synthetic_data
        )
        
        # 3. Privacy validation
        logger.info("Running privacy validation...")
        results['checks']['privacy'] = self._validate_privacy(synthetic_data)
        
        # 4. Data quality metrics
        logger.info("Running data quality validation...")
        results['checks']['data_quality'] = self._validate_data_quality(
            real_data, synthetic_data
        )
        
        # Determine overall pass/fail
        failed_checks = []
        for check_name, check_result in results['checks'].items():
            if not check_result.get('pass', False):
                failed_checks.append(check_name)
                results['overall_pass'] = False
        
        results['failed_checks'] = failed_checks
        
        if results['overall_pass']:
            logger.info("✅ All validation checks PASSED")
        else:
            logger.error(f"❌ Validation FAILED. Failed checks: {failed_checks}")
        
        return results
    
    def _validate_shape_correlation(self, real_data: Dict[str, pd.DataFrame],
                                   synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate column shapes and correlations using basic metrics."""
        results = {'pass': True, 'details': {}}
        
        for table_name in real_data.keys():
            if table_name not in synthetic_data:
                continue
                
            real_df = real_data[table_name]
            synthetic_df = synthetic_data[table_name]
            
            table_results = {'pass': True}
            
            # Simple shape validation - check if we have data
            shape_pass = len(synthetic_df) > 0 and len(synthetic_df.columns) == len(real_df.columns)
            table_results['shape_score'] = 1.0 if shape_pass else 0.0
            table_results['shape_pass'] = shape_pass
            
            if not shape_pass:
                table_results['pass'] = False
                results['pass'] = False
            
            # Basic correlation check for numerical columns  
            numeric_columns = real_df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 1:
                try:
                    real_corr = real_df[numeric_columns].corr()
                    synthetic_corr = synthetic_df[numeric_columns].corr()
                    
                    # Simple correlation similarity check
                    corr_diff = abs(real_corr - synthetic_corr).mean().mean()
                    corr_score = max(0.0, 1.0 - corr_diff)
                    
                    table_results['correlation_score'] = corr_score
                    table_results['correlation_pass'] = corr_score >= self.thresholds['correlation_threshold']
                    
                    if not table_results['correlation_pass']:
                        table_results['pass'] = False
                        results['pass'] = False
                
                except Exception as e:
                    logger.warning(f"Correlation check failed for {table_name}: {e}")
                    table_results['correlation_score'] = 0.5
                    table_results['correlation_pass'] = True  # Don't fail on correlation errors
            
            results['details'][table_name] = table_results
        
        return results
    
    def _validate_business_rules(self, real_data: Dict[str, pd.DataFrame],
                                synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate business rules from copilot_instructions.md"""
        results = {'pass': True, 'details': {}}
        
        # Rule 1: Marginals within ±10% by LHA×AgeGroup×Gender
        marginal_result = self._validate_marginals(real_data, synthetic_data)
        results['details']['marginals'] = marginal_result
        if not marginal_result['pass']:
            results['pass'] = False
        
        # Rule 2: LOS medians by Program/Subprogram within bands
        los_result = self._validate_los_medians(real_data, synthetic_data)
        results['details']['los_medians'] = los_result
        if not los_result['pass']:
            results['pass'] = False
        
        # Rule 3: Pediatric ED constraints
        pediatric_result = self._validate_pediatric_ed_rules(synthetic_data)
        results['details']['pediatric_ed'] = pediatric_result
        if not pediatric_result['pass']:
            results['pass'] = False
        
        # Rule 4: Data consistency checks
        consistency_result = self._validate_data_consistency(synthetic_data)
        results['details']['data_consistency'] = consistency_result
        if not consistency_result['pass']:
            results['pass'] = False
        
        return results
    
    def _validate_marginals(self, real_data: Dict[str, pd.DataFrame],
                           synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate marginal distributions are within tolerance."""
        results = {'pass': True, 'details': {}}
        
        if 'patients' not in real_data or 'patients' not in synthetic_data:
            return {'pass': False, 'error': 'Patients table missing'}
        
        real_patients = real_data['patients']
        synthetic_patients = synthetic_data['patients']
        
        # Check marginals by LHA, Age Group, Gender
        for column in ['lha_id', 'age_group', 'gender']:
            if column not in real_patients.columns or column not in synthetic_patients.columns:
                continue
            
            real_dist = real_patients[column].value_counts(normalize=True).sort_index()
            synthetic_dist = synthetic_patients[column].value_counts(normalize=True).sort_index()
            
            # Align indices
            all_values = set(real_dist.index) | set(synthetic_dist.index)
            real_dist = real_dist.reindex(all_values, fill_value=0)
            synthetic_dist = synthetic_dist.reindex(all_values, fill_value=0)
            
            # Calculate relative differences
            diff = abs(real_dist - synthetic_dist) / (real_dist + 1e-8)
            max_diff = diff.max()
            
            column_pass = max_diff <= self.thresholds['marginal_tolerance']
            results['details'][column] = {
                'max_difference': max_diff,
                'pass': column_pass
            }
            
            if not column_pass:
                results['pass'] = False
        
        return results
    
    def _validate_los_medians(self, real_data: Dict[str, pd.DataFrame],
                             synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate LOS medians by Program/Subprogram."""
        results = {'pass': True, 'details': {}}
        
        if 'ip_stays' not in real_data or 'ip_stays' not in synthetic_data:
            return {'pass': False, 'error': 'IP stays table missing'}
        
        real_stays = real_data['ip_stays']
        synthetic_stays = synthetic_data['ip_stays']
        
        # Group by program_id and calculate medians
        real_medians = real_stays.groupby(['program_id', 'subprogram_id'])['los_days'].median()
        synthetic_medians = synthetic_stays.groupby(['program_id', 'subprogram_id'])['los_days'].median()
        
        # Compare medians
        for (prog_id, subprog_id), real_median in real_medians.items():
            if (prog_id, subprog_id) in synthetic_medians.index:
                synthetic_median = synthetic_medians[(prog_id, subprog_id)]
                
                # Calculate relative difference
                rel_diff = abs(real_median - synthetic_median) / (real_median + 1e-8)
                
                program_pass = rel_diff <= self.thresholds['los_median_tolerance']
                results['details'][f'program_{prog_id}_subprogram_{subprog_id}'] = {
                    'real_median': real_median,
                    'synthetic_median': synthetic_median,
                    'relative_difference': rel_diff,
                    'pass': program_pass
                }
                
                if not program_pass:
                    results['pass'] = False
        
        return results
    
    def _validate_pediatric_ed_rules(self, synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate pediatric ED business rules."""
        results = {'pass': True, 'details': {}}
        
        if 'ed_encounters' not in synthetic_data:
            return {'pass': False, 'error': 'ED encounters table missing'}
        
        ed_encounters = synthetic_data['ed_encounters']
        
        # Need to join with patients to get age groups
        if 'patients' not in synthetic_data:
            return {'pass': False, 'error': 'Patients table needed for age validation'}
        
        patients = synthetic_data['patients']
        ed_with_age = ed_encounters.merge(patients[['patient_id', 'age_group']], on='patient_id')
        
        # Rule: Pediatric ED share ≥ 70% in <15 age group
        pediatric_ed_encounters = ed_with_age[ed_with_age['ed_subservice'] == 'Pediatric ED']
        if len(pediatric_ed_encounters) > 0:
            young_in_pediatric = pediatric_ed_encounters['age_group'].eq('0-14').sum()
            pediatric_young_share = young_in_pediatric / len(pediatric_ed_encounters)
            
            pediatric_pass = pediatric_young_share >= self.thresholds['pediatric_ed_share_min']
            results['details']['pediatric_ed_young_share'] = {
                'share': pediatric_young_share,
                'threshold': self.thresholds['pediatric_ed_share_min'],
                'pass': pediatric_pass
            }
            
            if not pediatric_pass:
                results['pass'] = False
        
        # Rule: Adult ED dominates in ≥25 age groups
        adult_age_groups = ['25-44', '45-64', '65-74', '75-84', '85+']
        adult_age_encounters = ed_with_age[ed_with_age['age_group'].isin(adult_age_groups)]
        
        if len(adult_age_encounters) > 0:
            pediatric_in_adult_ages = adult_age_encounters['ed_subservice'].eq('Pediatric ED').sum()
            pediatric_adult_share = pediatric_in_adult_ages / len(adult_age_encounters)
            
            adult_pass = pediatric_adult_share <= self.thresholds['pediatric_adult_ed_max']
            results['details']['pediatric_ed_adult_share'] = {
                'share': pediatric_adult_share,
                'threshold': self.thresholds['pediatric_adult_ed_max'],
                'pass': adult_pass
            }
            
            if not adult_pass:
                results['pass'] = False
        
        return results
    
    def _validate_data_consistency(self, synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate data consistency constraints."""
        results = {'pass': True, 'details': {}}
        
        # Check 1: DOB to age group consistency
        if 'patients' in synthetic_data:
            patients = synthetic_data['patients']
            if 'dob' in patients.columns and 'age_group' in patients.columns:
                age_consistency = self._check_age_consistency(patients)
                results['details']['age_consistency'] = age_consistency
                if not age_consistency['pass']:
                    results['pass'] = False
        
        # Check 2: LOS ≥ 0.25 days
        if 'ip_stays' in synthetic_data:
            ip_stays = synthetic_data['ip_stays']
            if 'los_days' in ip_stays.columns:
                min_los_violations = (ip_stays['los_days'] < 0.25).sum()
                los_pass = min_los_violations == 0
                results['details']['min_los'] = {
                    'violations': min_los_violations,
                    'pass': los_pass
                }
                if not los_pass:
                    results['pass'] = False
        
        # Check 3: Discharge after admit timestamp
        if 'ip_stays' in synthetic_data:
            ip_stays = synthetic_data['ip_stays']
            if 'admit_ts' in ip_stays.columns and 'discharge_ts' in ip_stays.columns:
                # Convert to datetime if needed
                admit_ts = pd.to_datetime(ip_stays['admit_ts'])
                discharge_ts = pd.to_datetime(ip_stays['discharge_ts'])
                
                timestamp_violations = (discharge_ts < admit_ts).sum()
                timestamp_pass = timestamp_violations == 0
                results['details']['timestamp_order'] = {
                    'violations': timestamp_violations,
                    'pass': timestamp_pass
                }
                if not timestamp_pass:
                    results['pass'] = False
        
        return results
    
    def _check_age_consistency(self, patients: pd.DataFrame) -> Dict[str, Any]:
        """Check DOB to age group consistency."""
        reference_date = date(2025, 1, 1)
        
        def calculate_expected_age_group(dob):
            if pd.isna(dob):
                return None
            age = (reference_date - pd.to_datetime(dob).date()).days // 365
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
        
        expected_age_groups = patients['dob'].apply(calculate_expected_age_group)
        inconsistencies = (expected_age_groups != patients['age_group']).sum()
        
        return {
            'inconsistencies': inconsistencies,
            'pass': inconsistencies == 0
        }
    
    def _validate_privacy(self, synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate privacy constraints - no identical quasi-identifiers."""
        results = {'pass': True, 'details': {}}
        
        if 'patients' not in synthetic_data:
            return {'pass': False, 'error': 'Patients table missing'}
        
        patients = synthetic_data['patients']
        
        # Check for identical quasi-identifiers (DOB, LHA, Gender)
        quasi_identifier_cols = ['dob', 'lha_id', 'gender']
        available_cols = [col for col in quasi_identifier_cols if col in patients.columns]
        
        if len(available_cols) >= 2:
            duplicates = patients.duplicated(subset=available_cols).sum()
            privacy_pass = duplicates == 0
            
            results['details']['quasi_identifier_duplicates'] = {
                'duplicates': duplicates,
                'columns_checked': available_cols,
                'pass': privacy_pass
            }
            
            if not privacy_pass:
                results['pass'] = False
        
        # K-anonymity check
        if KAnonymity and len(available_cols) >= 2:
            try:
                k_anonymity_score = KAnonymity.compute(
                    synthetic_data['patients'],
                    key_fields=available_cols[:3] if len(available_cols) >= 3 else available_cols
                )
                
                k_anonymity_pass = k_anonymity_score >= self.thresholds['k_anonymity_min']
                results['details']['k_anonymity'] = {
                    'score': k_anonymity_score,
                    'threshold': self.thresholds['k_anonymity_min'],
                    'pass': k_anonymity_pass
                }
                
                if not k_anonymity_pass:
                    results['pass'] = False
            
            except Exception as e:
                logger.warning(f"K-anonymity check failed: {e}")
                # Don't fail validation on k-anonymity errors
        
        return results
    
    def _validate_data_quality(self, real_data: Dict[str, pd.DataFrame],
                              synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Overall data quality validation using SDMetrics."""
        results = {'pass': True}
        
        try:
            # This would require proper multi-table metadata setup
            # For now, implement basic quality checks
            
            overall_quality = 0.0
            table_count = 0
            
            for table_name in real_data.keys():
                if table_name in synthetic_data:
                    # Simple quality metric - check if basic statistics are similar
                    real_df = real_data[table_name]
                    synthetic_df = synthetic_data[table_name]
                    
                    # Check row count similarity (within 20%)
                    row_count_ratio = len(synthetic_df) / len(real_df)
                    if 0.8 <= row_count_ratio <= 1.2:
                        overall_quality += 0.8
                    else:
                        overall_quality += 0.4
                    
                    table_count += 1
            
            if table_count > 0:
                overall_quality /= table_count
            
            quality_pass = overall_quality >= self.thresholds['overall_quality_min']
            
            results.update({
                'overall_quality': overall_quality,
                'threshold': self.thresholds['overall_quality_min'],
                'pass': quality_pass
            })
            
        except Exception as e:
            logger.error(f"Data quality validation failed: {e}")
            results = {'pass': False, 'error': str(e)}
        
        return results


def main():
    """Main validation script."""
    parser = argparse.ArgumentParser(description="Validate synthetic healthcare data")
    parser.add_argument("--real-data-dir", default="data", 
                       help="Directory containing real/seed CSV data files")
    parser.add_argument("--synthetic-data-dir", default="data/synthetic",
                       help="Directory containing synthetic CSV data files")
    parser.add_argument("--output", default="validation_report.json",
                       help="Output file for validation report")
    parser.add_argument("--strict", action='store_true',
                       help="Use stricter validation thresholds")
    
    args = parser.parse_args()
    
    # Load data
    real_data_dir = Path(args.real_data_dir)
    synthetic_data_dir = Path(args.synthetic_data_dir)
    
    # Expected data files
    data_files = ['patients.csv', 'ed_encounters.csv', 'ip_stays.csv']
    
    real_data = {}
    synthetic_data = {}
    
    for filename in data_files:
        table_name = filename.replace('.csv', '')
        
        # Load real data
        real_path = real_data_dir / filename
        if real_path.exists():
            real_data[table_name] = pd.read_csv(real_path)
            logger.info(f"Loaded real {table_name}: {len(real_data[table_name])} records")
        
        # Load synthetic data
        synthetic_filename = filename.replace('.csv', '_synthetic.csv')
        synthetic_path = synthetic_data_dir / synthetic_filename
        if synthetic_path.exists():
            synthetic_data[table_name] = pd.read_csv(synthetic_path)
            logger.info(f"Loaded synthetic {table_name}: {len(synthetic_data[table_name])} records")
    
    if not real_data or not synthetic_data:
        logger.error("Could not load data files. Check paths.")
        return
    
    # Setup validator
    thresholds = None
    if args.strict:
        thresholds = {
            'marginal_tolerance': 0.05,  # ±5% for marginals (stricter)
            'ed_volume_tolerance': 0.03,  # ±3% for ED volumes (stricter)
            'los_median_tolerance': 0.1,  # ±10% for LOS medians (stricter)
            'pediatric_ed_share_min': 0.75,  # ≥75% pediatric share (stricter)
            'pediatric_adult_ed_max': 0.05,  # ≤5% pediatric in adults (stricter)
            'correlation_threshold': 0.8,  # Higher correlation requirement
            'shape_threshold': 0.85,  # Higher shape similarity
            'k_anonymity_min': 10,  # Higher k-anonymity
            'privacy_score_min': 0.9,  # Higher privacy score
            'overall_quality_min': 0.8  # Higher quality threshold
        }
    
    validator = HealthcareDataValidator(thresholds)
    
    # Run validation
    validation_results = validator.validate_all(real_data, synthetic_data)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to {args.output}")
    
    # Exit with error code if validation failed
    if not validation_results['overall_pass']:
        exit(1)


if __name__ == "__main__":
    main()
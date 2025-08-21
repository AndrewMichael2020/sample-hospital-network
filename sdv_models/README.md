# SDV (Synthetic Data Vault) Implementation

This directory contains the implementation of SDV for generating higher-order correlations between healthcare data tables.

## Overview

The SDV implementation provides multi-table synthetic data generation using the HMA1 (Hierarchical Modeling Algorithm) to maintain referential integrity and cross-table correlations between:

- **Patients** (parent table) - patient demographics and characteristics
- **ED_Encounters** (child table) - emergency department visits linked to patients
- **IP_Stays** (child table) - inpatient stays linked to patients

## Files

### Core SDV Files

- **`metadata.json`** - Multi-table metadata defining table schemas, data types, and relationships
- **`constraints.py`** - Business rule validation and data correction functions
- **`train.py`** - HMA1/CTGAN model training and synthetic data generation
- **`validate.py`** - Quality gates and privacy validation for synthetic data

## Usage

### Quick Start with Make

```bash
# Complete SDV pipeline
make sdv-pipeline

# Individual steps
make sdv-train      # Train HMA1 model on seed data
make sdv-generate   # Generate synthetic data from trained model  
make sdv-validate   # Validate synthetic data quality
```

### Manual Usage

#### 1. Train SDV Model

```bash
# Train HMA1 model with default settings
python sdv_models/train.py --model-type hma --epochs 100 --patients 2000

# Train with custom parameters
python sdv_models/train.py \
  --data-dir data \
  --model-type hma \
  --epochs 200 \
  --patients 5000 \
  --save-name my_healthcare_model
```

#### 2. Generate Synthetic Data

```bash
# Generate using existing model
python sdv_models/train.py --generate-only --patients 10000 --save-name healthcare_model

# Or specify custom model
python sdv_models/train.py --generate-only --patients 5000 --save-name my_healthcare_model
```

#### 3. Validate Data Quality

```bash
# Basic validation
python sdv_models/validate.py

# Strict validation with tighter thresholds
python sdv_models/validate.py --strict --output strict_validation.json
```

## Business Rules & Constraints

The SDV implementation enforces several healthcare-specific business rules:

### Data Consistency
- **Age-DOB Consistency**: Age groups automatically calculated from date of birth
- **LOS Minimum**: Length of stay ≥ 0.25 days for all inpatient stays
- **Timestamp Order**: Discharge timestamp after admit timestamp
- **ALC Constraint**: Alternative Level of Care patients have LOS ≥ 1.0 days

### Clinical Business Rules  
- **Pediatric ED**: ≥70% of Pediatric ED visits for age groups 0-14/15-24
- **Adult ED Dominance**: ≤10% Pediatric ED usage for adult age groups (25+)
- **Marginal Distributions**: Within ±10% of original for LHA×Age×Gender
- **LOS Medians**: Within ±15% of original by Program/Subprogram

### Privacy Constraints
- **Unique Quasi-identifiers**: No duplicate (DOB, LHA, Gender) combinations  
- **K-anonymity**: Minimum k=5 for key demographic combinations

## Model Types

### HMA1 (Recommended)
- **Multi-table**: Preserves cross-table relationships and referential integrity
- **Hierarchical**: Models parent-child table dependencies  
- **Quality**: Best for maintaining complex correlations
- **Performance**: Slower training but higher quality output

### CTGAN (Alternative)
- **Single-table**: Trains separate models per table
- **Independent**: No cross-table relationship preservation
- **Quality**: Good for individual table modeling
- **Performance**: Faster training, lower cross-table fidelity

## Output

### Generated Files
- **`data/synthetic/`** - Directory containing synthetic data CSV files
  - `patients_synthetic.csv` - Synthetic patient records
  - `ed_encounters_synthetic.csv` - Synthetic ED encounters
  - `ip_stays_synthetic.csv` - Synthetic inpatient stays
  - `quality_report.json` - Basic quality metrics

### Model Artifacts
- **`sdv_models/trained_models/`** - Directory for trained model files (*.pkl)
- **Metadata backups** - JSON metadata saved with each model

### Validation Reports
- **`validation_report.json`** - Comprehensive validation results
- **Business rule checks** - Pass/fail status for each constraint
- **Quality metrics** - Shape, correlation, and privacy scores
- **Privacy analysis** - K-anonymity and uniqueness validation

## Configuration

### Quality Thresholds (Default)
```python
{
    'marginal_tolerance': 0.1,      # ±10% for demographic distributions
    'ed_volume_tolerance': 0.05,    # ±5% for ED volumes  
    'los_median_tolerance': 0.15,   # ±15% for LOS medians
    'pediatric_ed_share_min': 0.7,  # ≥70% pediatric share in <15
    'pediatric_adult_ed_max': 0.1,  # ≤10% pediatric in ≥25
    'correlation_threshold': 0.7,   # Minimum correlation preservation
    'shape_threshold': 0.8,         # Minimum shape similarity  
    'k_anonymity_min': 5,          # Minimum k-anonymity
    'overall_quality_min': 0.75    # Minimum overall quality
}
```

### Strict Mode
Use `--strict` flag for tighter validation thresholds suitable for production use.

## Privacy & Compliance

- **Fictional Data Only**: All generated data is synthetic and fictional
- **No PHI Training**: Models are trained only on rule-based pseudo-seed data
- **Privacy Validation**: Automatic checks for memorization and uniqueness
- **Model Storage**: Trained models stored locally (not exported per instructions)

As stated in copilot_instructions.md: *"Do not export models trained on any real PHI"*

## Advanced Usage

### Custom Constraints

Add custom business rules by modifying `constraints.py`:

```python
def validate_custom_rule(data: pd.DataFrame) -> pd.Series:
    """Custom validation logic."""
    return data['custom_field'].apply(lambda x: x > 0)
```

### Post-Processing Corrections

Apply automatic corrections to ensure compliance:

```python
corrected_data = apply_data_corrections(synthetic_data, 'patients')
```

### Model Comparison

Train multiple model types and compare quality:

```bash
# Train HMA1 model
python sdv_models/train.py --model-type hma --save-name hma_model

# Train CTGAN models  
python sdv_models/train.py --model-type ctgan --save-name ctgan_model

# Compare validation results
python sdv_models/validate.py --output hma_validation.json
```

## Troubleshooting

### Memory Issues
- Reduce `--patients` parameter for smaller datasets
- Use fewer `--epochs` for faster training
- Train on subsets of tables if needed

### Quality Issues
- Increase `--epochs` for better model training
- Check business rule compliance in validation report
- Adjust quality thresholds if needed
- Use larger seed datasets for training

### Privacy Concerns
- Run validation with `--strict` mode
- Check k-anonymity scores in validation report
- Verify no quasi-identifier duplicates exist

## Integration

The synthetic data can be used for:

- **Testing**: Realistic test datasets for application development
- **Analytics**: Safe data for business intelligence and reporting  
- **ML Training**: Training datasets for machine learning models
- **Data Sharing**: Shareable datasets for research and collaboration

Connect to existing workflows via standard CSV format compatible with MySQL, Power BI, and other analytics tools.
# Synthetic Healthcare Database

**⚠️ This data is entirely synthetic and fictional, generated for non-production testing and development purposes only.**

This project creates and populates a MySQL database with synthetic healthcare data for a fictional Lower Mainland hospital network. The data includes facilities, patients, emergency department encounters, inpatient stays, and population projections.

## Quick Start

### Prerequisites
- Python 3.8+
- MySQL 8.0+ (running and accessible)
- Basic MySQL user with database creation privileges

### Option 1: Automated Setup
```bash
# Install dependencies and run complete setup
pip install -r requirements.txt
python setup.py

# Or with custom MySQL connection
python setup.py --host localhost --user myuser --password mypass
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
make setup

# 2. Create database schema
mysql -e "CREATE DATABASE IF NOT EXISTS lm_synth CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
mysql lm_synth < schema.sql

# 3. Generate sample data
make generate

# 4. Load data into MySQL
make load
```

## Database Schema

The database contains the following tables:

### Dimension Tables
- **dim_site**: 12 fictional hospital facilities (e.g., "Snowberry General", "Blue Heron Medical")
- **dim_program**: 16 healthcare programs (Medicine, Surgery, Emergency, etc.)  
- **dim_subprogram**: 3 subprograms for each program
- **dim_lha**: 12 fictional Local Health Areas mapped to default facilities

### Reference Tables
- **population_projection**: Population forecasts by year (2025-2034), LHA, age group, and gender
- **ed_baseline_rates**: Emergency department utilization rates per 1000 population

### Fact Tables
- **patients**: ~1000 synthetic patients with demographics and home facilities
- **ed_encounters**: Emergency department visits with timestamps, acuity, disposition
- **ip_stays**: Inpatient stays with length of stay, programs, ALC flags

## Sample Data Characteristics

- **Facilities**: 12 fictional Lower Mainland hospitals with codes like LM-SNW, LM-BLH
- **LHAs**: 12 fictional areas like "Harborview", "Riverbend", "Cedar Heights"
- **Patients**: 1000 synthetic patients with realistic age/gender distributions
- **Encounters**: ~2000 ED visits with age-appropriate service assignment
- **Geography**: 90% of care occurs at patients' home facility, 10% cross-boundary care

### Age Group Distribution
- Pediatric ED encounters concentrated in 0-14 age groups
- Adult ED encounters predominantly 25+ age groups  
- Elderly (75+) patients have higher ED rates and longer inpatient stays

## Sample Queries

### Facility Summary
```sql
SELECT site_code, site_name, COUNT(p.patient_id) as patient_count
FROM dim_site s
LEFT JOIN patients p ON s.site_id = p.facility_home_id  
GROUP BY s.site_id, s.site_code, s.site_name
ORDER BY patient_count DESC;
```

### ED Volume Projection for 2025
```sql
SELECT s.site_code AS facility,
       r.ed_subservice,
       ROUND(SUM(p.population * r.baserate_per_1000 / 1000.0), 0) AS projected_volumes
FROM population_projection p
JOIN ed_baseline_rates r
  ON p.lha_id=r.lha_id AND p.age_group=r.age_group AND p.gender=r.gender
JOIN dim_lha l ON l.lha_id=p.lha_id
JOIN dim_site s ON s.site_id=l.default_site_id
WHERE p.year=2025
GROUP BY s.site_code, r.ed_subservice
ORDER BY projected_volumes DESC;
```

### Patient Demographics
```sql
SELECT age_group, gender, COUNT(*) as patient_count
FROM patients 
GROUP BY age_group, gender
ORDER BY age_group, gender;
```

## File Structure

```
.
├── requirements.txt          # Python dependencies
├── schema.sql               # MySQL DDL for all tables
├── generate_data.py         # Creates synthetic data as CSV files
├── load_data.py            # Loads CSV files into MySQL
├── setup.py               # Automated setup script
├── Makefile              # Build automation
├── README.md            # This documentation
└── data/               # Generated CSV files
    ├── dim_site.csv
    ├── dim_program.csv
    ├── patients.csv
    ├── ed_encounters.csv
    └── ...
```

## Customization

### Generating More/Fewer Patients
Edit `generate_data.py` and change the `n_patients` parameter in the `main()` function, or modify the script to accept command line arguments.

### Different Growth Rates
Modify the population projection logic in `generate_population_projection()` to adjust annual growth rates by LHA.

### Additional Programs
Add more programs to the `PROGRAMS` constant and corresponding subprograms to `SUBPROGRAMS`.

## Data Quality & Validation

The generated data includes:
- ✅ Consistent foreign key relationships
- ✅ Age-appropriate service assignments (pediatric vs adult ED)
- ✅ Realistic length of stay distributions
- ✅ Higher ALC rates for elderly and medicine patients
- ✅ Seasonal and demographic variation in utilization rates

## Privacy & Compliance

- **All data is completely synthetic** - no real patient information
- Facility names and LHA names are entirely fictional
- Patient IDs are randomly generated UUIDs
- No real addresses, names, or identifiable information

## Troubleshooting

### MySQL Connection Issues
```bash
# Test MySQL connectivity
mysql -h localhost -u root -p -e "SELECT 1;"

# Check if database exists
mysql -h localhost -u root -p -e "SHOW DATABASES LIKE 'lm_synth';"
```

### Missing Data Files
```bash
# Regenerate data files
make clean
make generate
```

### Foreign Key Constraint Errors
The loading order matters due to foreign key relationships. The `load_data.py` script loads tables in the correct dependency order.

## Development

### Running Tests
```bash
make test
```

### Generate Small Dataset
```bash
# Modify generate_data.py for fewer patients for faster testing
python -c "
import generate_data
# Edit the main() function call to use fewer patients
"
```

---

**Note**: This is synthetic data for development and testing purposes only. Do not use in production environments or for real healthcare decisions.
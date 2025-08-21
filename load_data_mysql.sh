#!/bin/bash
# load_data_mysql.sh - Load CSV data using MySQL LOAD DATA LOCAL INFILE

DB="lm_synth"
DATA_DIR="data"

echo "Loading data into MySQL database: $DB"

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory '$DATA_DIR' not found. Run generate_data.py first."
    exit 1
fi

# Function to load CSV with proper error handling
load_table() {
    local table=$1
    local csv_file=$2
    local columns=$3
    
    echo "Loading $csv_file into $table..."
    
    if [ ! -f "$DATA_DIR/$csv_file" ]; then
        echo "Warning: $csv_file not found, skipping $table"
        return 1
    fi
    
    # Create LOAD DATA SQL
    sql="
    LOAD DATA LOCAL INFILE '$PWD/$DATA_DIR/$csv_file'
    INTO TABLE $table
    FIELDS TERMINATED BY ',' ENCLOSED BY '\"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    $columns;
    "
    
    mysql --defaults-file=/etc/mysql/debian.cnf --local-infile=1 $DB -e "$sql"
    
    if [ $? -eq 0 ]; then
        echo "  Successfully loaded $table"
        mysql --defaults-file=/etc/mysql/debian.cnf $DB -e "SELECT COUNT(*) as count FROM $table;" | tail -n 1 | xargs -I {} echo "  Row count: {}"
        return 0
    else
        echo "  Error loading $table"
        return 1
    fi
}

# Enable local_infile
mysql --defaults-file=/etc/mysql/debian.cnf $DB -e "SET GLOBAL local_infile=1;"

# Load dimension tables first (order matters due to foreign keys)
load_table "dim_site" "dim_site.csv" "(site_code, site_name)"
load_table "dim_program" "dim_program.csv" "(program_id, program_name)"  
load_table "dim_subprogram" "dim_subprogram.csv" "(program_id, subprogram_id, subprogram_name)"
load_table "dim_lha" "dim_lha.csv" "(lha_name, default_site_id)"

# Load reference tables
load_table "population_projection" "population_projection.csv" "(year, lha_id, age_group, gender, population)"
load_table "ed_baseline_rates" "ed_baseline_rates.csv" "(lha_id, age_group, gender, ed_subservice, baserate_per_1000)"

# Load fact tables
load_table "patients" "patients.csv" "(patient_id, lha_id, facility_home_id, age_group, gender, dob, primary_ed_subservice, expected_ed_rate, ed_visits_year)"
load_table "ed_encounters" "ed_encounters.csv" "(encounter_id, patient_id, facility_id, ed_subservice, arrival_ts, acuity, dispo)"
load_table "ip_stays" "ip_stays.csv" "(stay_id, patient_id, facility_id, program_id, subprogram_id, admit_ts, discharge_ts, los_days, alc_flag)"

echo ""
echo "Data loading completed!"
echo ""

# Verification queries
echo "=== Data Verification ==="
mysql --defaults-file=/etc/mysql/debian.cnf $DB -e "
SELECT 'Facilities' as Table_Name, COUNT(*) as Row_Count FROM dim_site
UNION ALL
SELECT 'Programs', COUNT(*) FROM dim_program
UNION ALL
SELECT 'Subprograms', COUNT(*) FROM dim_subprogram
UNION ALL
SELECT 'LHAs', COUNT(*) FROM dim_lha
UNION ALL
SELECT 'Population', COUNT(*) FROM population_projection
UNION ALL
SELECT 'ED_Rates', COUNT(*) FROM ed_baseline_rates
UNION ALL
SELECT 'Patients', COUNT(*) FROM patients
UNION ALL
SELECT 'ED_Encounters', COUNT(*) FROM ed_encounters
UNION ALL
SELECT 'IP_Stays', COUNT(*) FROM ip_stays;
"

echo ""
echo "=== Sample Facilities ==="
mysql --defaults-file=/etc/mysql/debian.cnf $DB -e "SELECT site_code, site_name FROM dim_site LIMIT 5;"

echo ""
echo "=== Sample ED Projection for 2025 ==="
mysql --defaults-file=/etc/mysql/debian.cnf $DB -e "
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
ORDER BY projected_volumes DESC
LIMIT 10;
"

echo ""
echo "Healthcare database is ready for use!"
echo "To connect: mysql --defaults-file=/etc/mysql/debian.cnf lm_synth"
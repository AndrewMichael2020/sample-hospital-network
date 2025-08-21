
# Create Synthetic Healthcare Dataset — Generate data & MySQL Persistence: Blueprint

**Goal:** Generate **realistic, non‑PHI synthetic data** for the **Lower Mainland region** to prototype clinical service forecasting (12 facilities × 16 programs × 3 subprograms) and ED projections — and **persist the outputs to MySQL** on a GCP VM.  
**Audience:** Data analysts/engineers using GitHub Copilot, Codespaces, Microsoft Fabric, and Power BI.

> **Naming rule:** All facility sites and geographic areas in this blueprint are **fictional** (and slightly hilarious but graceful). Do **not** use real names or codes.

---

## 1) High‑level approach (choose A, or A→B)

### A) Rule‑based generator (recommended v1)
Encode region‑like **distributions** and **constraints** in YAML: age, gender, local health areas (LHAs), facility mapping, 10‑year population growth, ED baseline rates by segment, IP length‑of‑stay (LOS) by program, ALC rates, transfers, and seasonality.  
- **Counts:** Poisson/Negative Binomial  
- **Durations:** Lognormal/Gamma  
- **Categoricals:** configured probability vectors

**Pros:** transparent, deterministic, easy to tune for policy scenarios.  
**Cons:** correlation structure only as rich as you encode.

### B) Model‑based generator (SDV multi‑table) (optional uplift)
Train **SDV** (HMA1 / CTGAN / TVAE / GaussianCopula) on a **pseudo‑seed** produced by (A), with PK/FK metadata and explicit constraints. Use this when you need higher‑order correlations between tables.  
**Important:** Do *not* train on real PHI; if you ever do, keep models private and run privacy checks (sdmetrics).

---

## 2) Data model (tables, keys, volumes)

### Dimensions
- **DimSite**: 12 **fictional facilities** (codes + names).  
- **DimProgram** (16) & **DimSubprogram** (3 each).  
- **DimLHA** (≈12 **fictional local areas**) with a **default_site_id** mapping.  
- **DimAgeGroup**: `0‑4, 5‑14, 15‑24, 25‑44, 45‑64, 65‑74, 75‑84, 85+`.  
- **DimGender**: `Female, Male, Other`.  
- **DimDate/Fiscal**: for 10‑year horizon.  
- **DimScenario** (optional): scenario parameters for on‑demand forecasts.

### Fact / Reference
- **PopulationProjection** (Year, LHA, AgeGroup, Gender, Population).  
- **ED_BaselineRates** (LHA, AgeGroup, Gender, ED_subservice, Baserate_per_1000).  
- **Patients** (PatientID, DOB, AgeGroup, Gender, LHA, FacilityHome, …) ~**50,000**.  
- **ED_Encounters** (EncounterID, PatientID, Facility, ED_subservice, ArrivalTS, Acuity, Dispo).  
- **IP_Stays** (optional) (StayID, PatientID, Facility, Program, Subprogram, AdmitTS, DischargeTS, LOS, ALC_flag).  
- **CapacityDaily** (optional): (Date, Site, StaffedBeds, PhysicalBeds, NHPPD).

### Keys & relationships
- `DimSite.site_id` ← Patients.facility_home_id, ED_Encounters.facility_id, IP_Stays.facility_id  
- `DimProgram/DimSubprogram` ← IP_Stays  
- `Patients.PatientID` ← ED_Encounters.PatientID, IP_Stays.PatientID  
- `DimLHA.lha_id` ← Patients.lha_id ← PopulationProjection.lha_id ← ED_BaselineRates.lha_id

---

## 3) Fictional facilities & LHAs (examples)

### Facilities (12)
- **LM‑SNW** — Snowberry General  
- **LM‑BLH** — Blue Heron Medical  
- **LM‑SLM** — Salmon Run Hospital  
- **LM‑MSC** — Mossy Cedar Community  
- **LM‑OTB** — Otter Bay Medical Centre  
- **LM‑BRC** — Bear Creek Hospital  
- **LM‑DFT** — Driftwood Regional  
- **LM‑STG** — Stargazer Health Centre  
- **LM‑SRC** — Sunrise Coast Hospital  
- **LM‑GRS** — Grouse Ridge Medical  
- **LM‑FGH** — Foggy Harbor Hospital  
- **LM‑GPK** — Granite Peak Medical

### LHAs (12) — map each to a default facility
- Harborview → LM‑FGH  
- Riverbend → LM‑BRC  
- North Shoreline → LM‑GRS  
- Cedar Heights → LM‑MSC  
- Lakeside Plains → LM‑SNW  
- Granite Hills → LM‑GPK  
- Sunset Promenade → LM‑SRC  
- Driftwood Inlet → LM‑DFT  
- Otter Cove → LM‑OTB  
- Blueberry Meadows → LM‑BLH  
- Silver Falls → LM‑SLM  
- Stargazer Valley → LM‑STG

> Allow **5–10% cross‑LHA care** (patients whose home facility ≠ default LHA facility).

---

## 4) Statistical design (defaults you can tune)

- **Population projections (10y):** Base counts by LHA (one or two are much larger), annual growth by LHA (0.6–2.0%).  
- **Age distribution:** weights per LHA; **Gender:** ~49/49/2.  
- **ED subservices:** `Adult ED`, `Pediatric ED`, `Urgent Care Centre`.  
- **ED rates/1000/year:** by AgeGroup × Gender × LHA × ED_subservice (elderly high for Adult ED; 0–14 high for Pediatric).  
- **Encounter counts:** ED visits per person via **Poisson**(λ) or **NegBin**(mean, k) to model over‑dispersion.  
- **IP LOS:** **Lognormal**(μ, σ) by Program/Subprogram (Medicine longer tails; Surgical shorter; Critical Care highest variance).  
- **ALC flag:** Bernoulli by age & program (higher in 75+ and Medicine/Palliative).  
- **Transfers:** Bernoulli with small p; define few corridors (e.g., LM‑SRC ↔ LM‑GRS).  
- **Seasonality:** monthly multipliers (pediatric winter spike; summer trauma bump).

**Hard constraints:**
- DOB ⇒ AgeGroup consistent with reference date.  
- LOS ≥ 0.25 days; ALC implies LOS ≥ threshold.  
- Keys unique; FK valid.  
- Pediatric ED encounters mostly `<18`; Adult ED dominates `≥25`.  
- Subprogram ∈ Program; Program available at Facility (coverage matrix).

---

## 5) Repository layout

```
lm-synth/
├─ src/
│  ├─ lm_synth/
│  │  ├─ __init__.py
│  │  ├─ config.py               # pydantic models for YAML config
│  │  ├─ dims.py                 # build DimSite/Program/Subprogram/LHA/Age/Gender/Date
│  │  ├─ population.py           # 10y projections from config growth
│  │  ├─ rules.py                # distributions & constraints
│  │  ├─ gen_patients.py         # ~50k patients
│  │  ├─ gen_ed.py               # ED encounters from rates (Poisson/NegBin)
│  │  ├─ gen_ip.py               # optional IP stays from LOS, ALC, transfers
│  │  ├─ validate.py             # sdmetrics + business-rule checks
│  │  ├─ export.py               # CSV/Parquet writers
│  │  └─ cli.py                  # click/typer CLI
│  └─ sdv_models/
│     ├─ metadata.json           # SDV multi-table metadata (HMA1) 
│     ├─ constraints.py          # SDV custom constraints
│     └─ train.py                # optional: fit HMA1/CTGAN on rule-based seed
├─ configs/
│  ├─ lower_mainland_defaults.yaml    # LHAs, growth%, age/gender weights, ED rates, LOS params
│  └─ coverage_matrix.csv             # which programs/subprograms exist at which sites
├─ out/                          # generated data
├─ tests/
│  ├─ test_keys.py               # PK/FK, uniqueness
│  ├─ test_distributions.py      # marginals/crosstabs thresholds
│  └─ test_privacy.py            # nearest-neighbour/pMSE if SDV used
├─ requirements.txt
├─ pyproject.toml
├─ Makefile
└─ README.md
```

**requirements.txt**
```
pandas
numpy
pyarrow
scipy
faker
pydantic
click
sdv
sdmetrics
sqlalchemy
pymysql
```

**Makefile**
```
setup: ; python -m pip install -r requirements.txt
generate: ; python -m lm_synth.cli generate --patients 50000 --start-year 2025 --years 10 --config ./configs/lower_mainland_defaults.yaml --out ./out --with-ed --with-ip --format parquet
validate: ; python -m lm_synth.cli validate --in ./out --config ./configs/lower_mainland_defaults.yaml
```

---

## 6) CLI contract (typer/click)

```
# Generate all dimension & fact tables
lm-synth generate \
  --patients 50000 \
  --start-year 2025 --years 10 \
  --config ./configs/lower_mainland_defaults.yaml \
  --out ./out \
  [--with-ed] [--with-ip] \
  [--format parquet|csv] \
  [--seed 42]

# Validate outputs
lm-synth validate \
  --in ./out \
  --config ./configs/lower_mainland_defaults.yaml \
  --ks-threshold 0.1 --corr-threshold 0.1
```

**Outputs:**
- `/out/dim_site.{parquet|csv}`, `/out/dim_program.*`, `/out/dim_subprogram.*`, `/out/dim_lha.*`  
- `/out/population_projection.*`, `/out/ed_baseline_rates.*`  
- `/out/patients.*`, `/out/ed_encounters.*`, `/out/ip_stays.*` (optional)

---

## 7) Validation & quality gates

- **Shape tests (sdmetrics):** Column shapes, correlations, detection metrics.  
- **Business rules:**
  - Marginals within ±5–10% of config targets for `LHA×AgeGroup×Gender`.  
  - ED volumes recomputed from `Population × Baserate` within ±5% by `Facility × ED_subservice`.  
  - LOS medians by Program/Subprogram within configured bands.  
  - Pediatric ED share ≥ 70% in `<15`; minimal in `≥25`.
- **Privacy (if SDV used):** nearest‑neighbour distance thresholds, pMSE; block memorization.

---

## 8) Using **SDV** (optional, for richer correlations)

1. **metadata.json:** multi‑table PK/FK for Patients (pk: PatientID), ED_Encounters (pk: EncounterID, fk: PatientID), IP_Stays (pk: StayID, fk: PatientID).  
2. **constraints.py:** Age from DOB; LOS ≥ 0.25; categorical enums for LHA, Facility, Program, Subprogram; referential constraints.  
3. Train **HMA1** (or CTGAN/TVAE) on rule‑based **pseudo‑seed**; sample larger populations.  
4. Run **validate.py**; keep only datasets that pass quality gates.  
5. Do not export models trained on any real PHI.

**Copilot prompt (SDV metadata):**  
> “Write SDV multi‑table metadata for Patients (pk: PatientID), ED_Encounters (pk: EncounterID, fk: PatientID), IP_Stays (pk: StayID, fk: PatientID). Include field dtypes, constraints for positive LOS, DOB dates, enums for fictional LHA, Facility, Program, Subprogram.”

---

## 9) Programs (16) with three subprograms each (example set)

1. **Medicine** → a) General Medicine  b) Hospitalist  c) ACE (Acute Care for Elderly)  
2. **Inpatient MHSU** → a) Adult Inpatient Psychiatry  b) Psychiatric High Acuity/ICU  c) Substance Use Stabilization  
3. **MICY** → a) Labour & Delivery  b) Post‑partum/Maternity  c) Inpatient Pediatrics  
4. **Critical Care** → a) ICU (Med‑Surg)  b) High Acuity/Step‑Down  c) Rapid Response/Outreach  
5. **Surgery / Periop** → a) Operating Room  b) PACU/Day Surgery  c) Surgical Inpatient Unit  
6. **Emergency** → a) Adult ED  b) Pediatric ED  c) Urgent Care Centre  
7. **Cardiac** → a) Interventional Cardiology (Cath/PCI)  b) Cardiac Surgery/CSU  c) Telemetry/Heart Failure  
8. **Renal** → a) In‑Centre Hemodialysis  b) Peritoneal Dialysis  c) Kidney Care Clinic  
9. **Rehabilitation** → a) Inpatient Rehab  b) Outpatient/Day Rehab  c) Stroke/ESD  
10. **Primary Health Care** → a) PCN Clinic  b) UPCC  c) Home Health  
11. **Chronic Disease Mgmt** → a) Diabetes Education  b) COPD/Asthma Clinic  c) Heart Failure Clinic  
12. **Population & Public Health** → a) Communicable Disease  b) Health Protection  c) Health Promotion/Screening  
13. **Palliative Care** → a) Acute Palliative Unit  b) Hospice/Community  c) Palliative Consult  
14. **Trauma** → a) ED/Trauma Bay  b) Trauma Ward/Step‑Down  c) Follow‑up Clinic  
15. **Specialized Community Services** → a) Seniors Outreach  b) Complex Chronic Mgmt  c) Community Palliative Support  
16. **Pain Services** → a) Acute Pain Service  b) Chronic Pain Clinic  c) Interventional Pain

---

## 10) Example SQL (projection join shape)

```sql
-- #population => PopulationProjection WHERE Year = @yr
-- #ED_visits_per_segment_baseline => ED_BaselineRates

SELECT s.site_code AS facility,
       r.ed_subservice,
       SUM(1.0 * p.population * r.baserate_per_1000 / 1000.0) AS projected_volumes
FROM population_projection p
JOIN ed_baseline_rates r
  ON p.lha_id = r.lha_id
 AND p.age_group = r.age_group
 AND p.gender   = r.gender
JOIN dim_lha l ON l.lha_id = p.lha_id
JOIN dim_site s ON s.site_id = l.default_site_id
WHERE p.year = 2025
GROUP BY s.site_code, r.ed_subservice
ORDER BY projected_volumes DESC;
```

---

## 11) GitHub Copilot prompts (copy/paste)

**Config & Pydantic models**  
> “Create `configs/lower_mainland_defaults.yaml` schema with *fictional* LHAs, growth%, age/gender weights, ED rates per 1,000 by LHA×AgeGroup×Gender×ED_subservice, LOS params per Program/Subprogram. Then write `src/lm_synth/config.py` using pydantic to load and validate this YAML.”

**Dimension builders**  
> “Generate `src/lm_synth/dims.py` functions to build DimSite (12 fictional facilities), DimProgram (16), DimSubprogram (3 each), DimLHA from YAML.”

**Population projections**  
> “Implement `population.py: project_population(config, start_year, years)` returning DataFrame(Year, LHA, AgeGroup, Gender, Population). Use growth% per LHA and age/gender weights.”

**Patients (50K)**  
> “Implement `gen_patients.py: generate_patients(n, population_2025, lha_to_site)` to sample PatientID, DOB, AgeGroup, Gender, LHA, FacilityHome with reproducible seed.”

**ED encounters**  
> “Implement `gen_ed.py: generate_ed_encounters(patients, ed_rates, year)`; sample per‑patient Poisson(λ) (from LHA×AgeGroup×Gender×ED_subservice); create encounter rows with timestamps, facility, acuity.”

**IP stays (optional)**  
> “Implement `gen_ip.py: generate_ip_stays(patients, los_params, program_coverage)`; sample admission probability by age/program; LOS lognormal; ALC Bernoulli; ensure FK integrity.”

**Validation**  
> “Write `validate.py` tests for PK/FK, KS distance for marginals, correlation drift, pediatric share checks, LOS bands, and a final pass/fail summary.”

**Export**  
> “Write `export.py` to output CSV and Parquet with schema, dtypes, and partition columns (Year, Site).”

**CLI**  
> “Create `cli.py` (typer) with commands `generate` and `validate`, arguments per Section 6. Include `--format` and `--seed`.”

**CI**  
> “Add `.github/workflows/ci.yml` to run `make setup generate validate` on PRs; upload `/out` as artifact.”

---

## 12) Privacy & compliance notes

- All names, facility codes, LHAs are **fictional**.  
- No PHI in repo or seeds. If SDV is ever trained on any real sample, keep models private and run privacy checks (nearest neighbour distance, pMSE).  
- Add a unit test that fails if any patient record appears twice with identical quasi‑identifiers (DOB, LHA, Gender).  
- README must state clearly **“synthetic, for non‑production testing”**.

---

## 13) Definition of Done (DoD)

- `make generate` creates all tables deterministically with a seed.  
- `make validate` passes with thresholds set in config.  
- Output ingests directly to Fabric (OneLake) & Power BI.  
- README documents schema, assumptions, and how to tune distributions.

---

## 14) Persist data in **MySQL** on a **GCP VM** (self‑managed) -- later. Right now save in csvs in the directory tofgether with the code.

**Goal:** Load generated CSV/Parquet into a MySQL 8.0 database running on your GCP VM so downstream tools can query it.

### 14.1 VM & network prep
1. VM OS: Ubuntu 22.04 LTS (or Debian).  
2. Firewall (VPC): allow **TCP 3306** **from trusted IPs only** (office/VPN). Avoid `0.0.0.0/0`.  
3. OS basics:
   ```bash
   sudo apt update && sudo apt -y upgrade
   sudo timedatectl set-timezone America/Vancouver
   ```

### 14.2 Install & configure MySQL 8.0
```bash
sudo apt -y install mysql-server
mysql --version
```
Secure and enable external access + fast loads:
```bash
sudo mysql_secure_installation

# /etc/mysql/mysql.conf.d/mysqld.cnf
sudo sed -i 's/^bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
echo -e "\n[mysqld]\nlocal_infile=ON\ncharacter-set-server=utf8mb4\ncollation-server=utf8mb4_0900_ai_ci" | sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql
```

### 14.3 Create DB and app user
```sql
-- On the VM: sudo mysql
CREATE DATABASE lm_synth CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'lm_app'@'%' IDENTIFIED WITH mysql_native_password BY 'REPLACE_ME_STRONG';
GRANT ALL PRIVILEGES ON lm_synth.* TO 'lm_app'@'%';
FLUSH PRIVILEGES;
```

### 14.4 DDL (tables & keys)
```sql
USE lm_synth;

-- Dimensions
CREATE TABLE dim_site (
  site_id INT AUTO_INCREMENT PRIMARY KEY,
  site_code VARCHAR(16) NOT NULL UNIQUE,
  site_name VARCHAR(128) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_program (
  program_id INT PRIMARY KEY,
  program_name VARCHAR(128) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_subprogram (
  program_id INT NOT NULL,
  subprogram_id INT NOT NULL,
  subprogram_name VARCHAR(128) NOT NULL,
  PRIMARY KEY (program_id, subprogram_id),
  CONSTRAINT fk_subprog_prog FOREIGN KEY (program_id) REFERENCES dim_program(program_id)
) ENGINE=InnoDB;

CREATE TABLE dim_lha (
  lha_id INT AUTO_INCREMENT PRIMARY KEY,
  lha_name VARCHAR(128) NOT NULL UNIQUE,
  default_site_id INT NOT NULL,
  CONSTRAINT fk_lha_site FOREIGN KEY (default_site_id) REFERENCES dim_site(site_id)
) ENGINE=InnoDB;

-- Population & rates
CREATE TABLE population_projection (
  year INT NOT NULL,
  lha_id INT NOT NULL,
  age_group VARCHAR(16) NOT NULL,
  gender ENUM('Female','Male','Other') NOT NULL,
  population INT NOT NULL,
  PRIMARY KEY (year, lha_id, age_group, gender),
  CONSTRAINT fk_pop_lha FOREIGN KEY (lha_id) REFERENCES dim_lha(lha_id)
) ENGINE=InnoDB;

CREATE TABLE ed_baseline_rates (
  lha_id INT NOT NULL,
  age_group VARCHAR(16) NOT NULL,
  gender ENUM('Female','Male','Other') NOT NULL,
  ed_subservice VARCHAR(48) NOT NULL,
  baserate_per_1000 DECIMAL(8,2) NOT NULL,
  PRIMARY KEY (lha_id, age_group, gender, ed_subservice),
  CONSTRAINT fk_rates_lha FOREIGN KEY (lha_id) REFERENCES dim_lha(lha_id)
) ENGINE=InnoDB;

-- Patients & encounters
CREATE TABLE patients (
  patient_id VARCHAR(24) PRIMARY KEY,
  lha_id INT NOT NULL,
  facility_home_id INT NOT NULL,
  age_group VARCHAR(16) NOT NULL,
  gender ENUM('Female','Male','Other') NOT NULL,
  dob DATE NOT NULL,
  primary_ed_subservice VARCHAR(48) NOT NULL,
  expected_ed_rate DECIMAL(8,4) NOT NULL,
  ed_visits_year INT NOT NULL,
  CONSTRAINT fk_pat_lha FOREIGN KEY (lha_id) REFERENCES dim_lha(lha_id),
  CONSTRAINT fk_pat_site FOREIGN KEY (facility_home_id) REFERENCES dim_site(site_id),
  INDEX idx_pat_lha (lha_id),
  INDEX idx_pat_site (facility_home_id)
) ENGINE=InnoDB;

CREATE TABLE ed_encounters (
  encounter_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  patient_id VARCHAR(24) NOT NULL,
  facility_id INT NOT NULL,
  ed_subservice VARCHAR(48) NOT NULL,
  arrival_ts DATETIME NOT NULL,
  acuity TINYINT,
  dispo VARCHAR(32),
  CONSTRAINT fk_ed_pat FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
  CONSTRAINT fk_ed_site FOREIGN KEY (facility_id) REFERENCES dim_site(site_id),
  INDEX idx_ed_patient (patient_id),
  INDEX idx_ed_arrival (arrival_ts)
) ENGINE=InnoDB;

CREATE TABLE ip_stays (
  stay_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  patient_id VARCHAR(24) NOT NULL,
  facility_id INT NOT NULL,
  program_id INT NOT NULL,
  subprogram_id INT NOT NULL,
  admit_ts DATETIME NOT NULL,
  discharge_ts DATETIME,
  los_days DECIMAL(6,2) NOT NULL,
  alc_flag TINYINT(1) NOT NULL DEFAULT 0,
  CONSTRAINT fk_ip_pat FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
  CONSTRAINT fk_ip_site FOREIGN KEY (facility_id) REFERENCES dim_site(site_id),
  CONSTRAINT fk_ip_prog FOREIGN KEY (program_id) REFERENCES dim_program(program_id),
  CONSTRAINT fk_ip_subprog FOREIGN KEY (program_id, subprogram_id) REFERENCES dim_subprogram(program_id, subprogram_id),
  INDEX idx_ip_patient (patient_id),
  INDEX idx_ip_admit (admit_ts)
) ENGINE=InnoDB;
```

### 14.5 Load data — fast path (`LOAD DATA LOCAL INFILE`)

1. Copy CSVs to the VM (e.g., `/opt/lm-synth/out`).  
2. Enable local loads on client:
   ```bash
   mysql --local-infile=1 -u lm_app -p -h 127.0.0.1 lm_synth
   ```
3. Example loads (adjust filenames/columns):
```sql
SET GLOBAL local_infile=1;

LOAD DATA LOCAL INFILE '/opt/lm-synth/out/dim_site.csv'
INTO TABLE dim_site
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(site_code, site_name);

LOAD DATA LOCAL INFILE '/opt/lm-synth/out/dim_program.csv'
INTO TABLE dim_program
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(program_id, program_name);

LOAD DATA LOCAL INFILE '/opt/lm-synth/out/dim_subprogram.csv'
INTO TABLE dim_subprogram
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(program_id, subprogram_id, subprogram_name);

-- If your population CSV has lha_name, stage & resolve to lha_id
CREATE TABLE IF NOT EXISTS _stg_population_name (
  year INT, lha_name VARCHAR(128), age_group VARCHAR(16),
  gender ENUM('Female','Male','Other'), population INT
);

LOAD DATA LOCAL INFILE '/opt/lm-synth/out/population_projection.csv'
INTO TABLE _stg_population_name
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

INSERT INTO population_projection (year, lha_id, age_group, gender, population)
SELECT s.year, l.lha_id, s.age_group, s.gender, s.population
FROM _stg_population_name s
JOIN dim_lha l ON l.lha_name = s.lha_name;
```

### 14.6 Load data — robust path (Python, CSV/Parquet)

```bash
python -m pip install pandas pyarrow sqlalchemy pymysql
```

```python
# load_to_mysql.py
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://lm_app:REPLACE_ME_STRONG@VM_IP:3306/lm_synth?charset=utf8mb4")

def load_csv(path, table, chunksize=100_000):
    for chunk in pd.read_csv(path, chunksize=chunksize):
        chunk.to_sql(table, engine, if_exists="append", index=False, method="multi")

def load_parquet(path, table, chunksize=100_000):
    df = pd.read_parquet(path)
    for i in range(0, len(df), chunksize):
        df.iloc[i:i+chunksize].to_sql(table, engine, if_exists="append", index=False, method="multi")

# Examples:
# load_csv("out/dim_site.csv", "dim_site")
# load_parquet("out/patients.parquet", "patients")
```

### 14.7 Verification
```sql
SELECT COUNT(*) FROM dim_site;
SELECT COUNT(*) FROM dim_program;
SELECT COUNT(*) FROM dim_subprogram;

-- ED projection check for a year
SELECT s.site_code AS facility,
       r.ed_subservice,
       SUM(p.population * r.baserate_per_1000 / 1000.0) AS projected_volumes
FROM population_projection p
JOIN ed_baseline_rates r
  ON p.lha_id=r.lha_id AND p.age_group=r.age_group AND p.gender=r.gender
JOIN dim_lha l ON l.lha_id=p.lha_id
JOIN dim_site s ON s.site_id=l.default_site_id
WHERE p.year=2025
GROUP BY s.site_code, r.ed_subservice
ORDER BY projected_volumes DESC;
```

### 14.8 Optional: Power BI / Fabric connectivity
- **Power BI Desktop** → Get Data → **MySQL** → `VM_IP`, Database `lm_synth`, User `lm_app`.  
- Ensure 3306 is open from your network/VPN; consider SSH tunnelling for defense‑in‑depth.

---

## 15) Copilot prompts for MySQL

- **DDL:**  
  > “Write MySQL 8.0 DDL for dim_site, dim_program, dim_subprogram, dim_lha, population_projection, ed_baseline_rates, patients, ed_encounters, ip_stays with PK/FK per blueprint; utf8mb4; InnoDB.”

- **Loader:**  
  > “Generate a Python script using pandas + SQLAlchemy (pymysql) to bulk‑load CSV/Parquet from ./out into MySQL lm_synth, including staging tables to resolve lha_name→lha_id.”

- **GCP bootstrap:**  
  > “Produce a bash script to install MySQL on Ubuntu, enable local_infile, open port 3306 to a CIDR, create lm_synth DB and lm_app user.”

---

**End of blueprint.**

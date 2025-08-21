
# Copilot Instructions — Adding to API & Data Layer (augment-only, non-destructive)
Date: 2025-08-21

**Goal**  
Add FTE + seasonality support via new **reference tables**, **seed data**, and **read-only API endpoints**, without changing or breaking the existing repository structure or workflows.

**Repository alignment (do not change existing)**  
- Keep current root files and flow: `schema.sql`, `generate_data.py`, `load_data.py`, `setup.py`, `Makefile`, `data/`, `sdv_models/`.  
- Database name stays **`lm_synth`**.  
- No renames/moves of existing files; only **additive** files or **append-only** edits.

---

## 0) Non‑destructive rules (important)
1. **Do not delete/rename** any existing tables, files, or Makefile targets.  
2. Prefer **new files** over modifying existing ones: add `schema_ext.sql`, `generate_refs.py`, `load_refs.py`, `api/` folder.  
3. If you must edit an existing file, make **append‑only** changes guarded with `IF NOT EXISTS` checks and comments starting with `-- EXTENSION:`.

---

## 1) Data prerequisites (reference tables to add)
Create a new file at repo root: **`schema_ext.sql`** with the following DDL. This file is applied **after** `schema.sql` and is safe to re-run.

```sql
-- EXTENSION: staffed beds schedule (selectable in UI as "Sched-A")
CREATE TABLE IF NOT EXISTS staffed_beds_schedule (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  site_id INT NOT NULL,
  program_id INT NOT NULL,
  schedule_code VARCHAR(32) NOT NULL, -- e.g., 'Sched-A'
  staffed_beds INT NOT NULL,
  UNIQUE KEY uq_sched (site_id, program_id, schedule_code),
  KEY idx_sched_site_prog (site_id, program_id)
);

-- EXTENSION: clinical baselines (per site/program/year)
CREATE TABLE IF NOT EXISTS clinical_baseline (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  site_id INT NOT NULL,
  program_id INT NOT NULL,
  baseline_year INT NOT NULL,      -- e.g., 2022
  los_base_days DECIMAL(6,3) NOT NULL,  -- acute LOS baseline
  alc_rate DECIMAL(6,4) NOT NULL,       -- fraction of pt-days (e.g., 0.12)
  UNIQUE KEY uq_baseline (site_id, program_id, baseline_year),
  KEY idx_baseline_site_prog (site_id, program_id)
);

-- EXTENSION: seasonality multipliers (month-level; global row via NULL site/program)
CREATE TABLE IF NOT EXISTS seasonality_monthly (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  site_id INT NULL,
  program_id INT NULL,
  month TINYINT NOT NULL CHECK (month BETWEEN 1 AND 12),
  multiplier DECIMAL(6,4) NOT NULL DEFAULT 1.0000,
  UNIQUE KEY uq_season (COALESCE(site_id, -1), COALESCE(program_id, -1), month),
  KEY idx_season_site_prog_month (site_id, program_id, month)
);

-- EXTENSION: staffing factors (optional; enables Nursing FTE calc)
CREATE TABLE IF NOT EXISTS staffing_factors (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  program_id INT NOT NULL,
  subprogram_id INT NULL,
  hppd DECIMAL(6,3) NOT NULL,                 -- hours per patient day
  annual_hours_per_fte INT NOT NULL DEFAULT 1950,
  productivity_factor DECIMAL(6,3) NOT NULL DEFAULT 0.90,
  UNIQUE KEY uq_staffing (program_id, COALESCE(subprogram_id, -1))
);
```

**Seed (illustrative, adjust later)** — place in a new file **`seed_ext.sql`** so you can load quickly:
```sql
INSERT INTO staffed_beds_schedule (site_id, program_id, schedule_code, staffed_beds)
VALUES (1,1,'Sched-A',80),(2,1,'Sched-A',70),(3,1,'Sched-A',62)
ON DUPLICATE KEY UPDATE staffed_beds=VALUES(staffed_beds);

INSERT INTO clinical_baseline (site_id, program_id, baseline_year, los_base_days, alc_rate)
VALUES (1,1,2022,6.0,0.12),(2,1,2022,5.8,0.11),(3,1,2022,5.6,0.10)
ON DUPLICATE KEY UPDATE los_base_days=VALUES(los_base_days), alc_rate=VALUES(alc_rate);

INSERT INTO seasonality_monthly (site_id, program_id, month, multiplier)
VALUES (NULL,NULL,1,1.00),(NULL,NULL,2,1.00),(NULL,NULL,3,1.02),(NULL,NULL,4,1.01),
       (NULL,NULL,5,1.00),(NULL,NULL,6,1.00),(NULL,NULL,7,0.98),(NULL,NULL,8,0.98),
       (NULL,NULL,9,1.01),(NULL,NULL,10,1.02),(NULL,NULL,11,1.03),(NULL,NULL,12,1.04)
ON DUPLICATE KEY UPDATE multiplier=VALUES(multiplier);

INSERT INTO staffing_factors (program_id, subprogram_id, hppd, annual_hours_per_fte, productivity_factor)
VALUES (1,NULL,6.5,1950,0.92)
ON DUPLICATE KEY UPDATE hppd=VALUES(hppd), annual_hours_per_fte=VALUES(annual_hours_per_fte), productivity_factor=VALUES(productivity_factor);
```

**Additive Makefile targets (optional, non-breaking)**
```Makefile
schema-ext:
\tmysql lm_synth < schema_ext.sql

seed-ext:
\tmysql lm_synth < seed_ext.sql
```

---

## 2) Compute model (single source of truth)
Let `g` = demand growth per year, `y` = years from baseline, `d` = LOS delta (decimal, e.g., -0.03), `occ_t` = occupancy target, `alc_t` = ALC target,
`alc_b` = baseline ALC, `LOS_b` = baseline LOS, `Adm_b` = baseline admissions (or derive from facts).

```
Adm    = Adm_b * (1+g)^y
LOS_acute = LOS_b * (1 + d)
LOS_eff   = LOS_acute * (1 + (alc_t - alc_b))
PtDays    = Adm * LOS_eff * seasonality_factor   # average or month-bucket as you prefer
Census    = PtDays / 365
ReqBeds   = Census / occ_t                       # round for display
Gap       = ReqBeds - StaffedBeds(site, program, schedule_code)

FTE (optional) = (ReqBeds * hppd * 365) / (annual_hours_per_fte * productivity_factor)

ED Boarding 95th (placeholder):
  Boarding95h = a + b*(occ_t - occ_ref) + c*(alc_t - alc_b) + e*d
```

**Bounds/guards**
- `occ_t ≥ 0.80`
- `LOS_eff ≥ 0.25 d`
- Missing staffing factors → return `NULL` for FTE in API.

**Baseline derivations from existing facts (examples)**
```sql
-- Baseline admissions per site/program/year (from ip_stays)
SELECT s.site_id, st.program_id, YEAR(st.admit_date) AS baseline_year,
       COUNT(*) AS admissions_base,
       AVG(st.length_of_stay_days) AS los_observed,
       AVG(CASE WHEN st.is_alc=1 THEN 1 ELSE 0 END) AS alc_rate_observed
FROM ip_stays st
JOIN dim_site s ON s.site_id = st.site_id
GROUP BY s.site_id, st.program_id, YEAR(st.admit_date);
```

---

## 3) Additive data generation & loading (keep originals intact)
**New script**: `generate_refs.py` (no changes to `generate_data.py`)  
- Emits CSVs under `data/` for: `staffed_beds_schedule.csv`, `clinical_baseline.csv`, `seasonality_monthly.csv`, `staffing_factors.csv`.  
- Values can be constants or simple randomization around the seeds above.

**New script**: `load_refs.py` (no changes to `load_data.py`)  
- Loads the four CSVs into the new tables in safe order.

**Additive Makefile targets (optional)**
```Makefile
generate-refs:
\tpython generate_refs.py

load-refs:
\tpython load_refs.py
```

---

## 4) Minimal API (new folder; does not touch existing scripts)
Add a new folder **`api/`** at repo root with these files:

```
api/
  main.py            # FastAPI app, CORS
  config.py          # reads MySQL env
  db.py              # async pool (asyncmy)
  schemas.py         # Pydantic DTOs
  repositories.py    # SQL selects for references and facts
  services.py        # compute functions from §2
```

**Dependencies** (append to `requirements.txt`, do not remove existing lines):  
`fastapi==0.115.*` `uvicorn[standard]==0.30.*` `pydantic==2.*` `pydantic-settings==2.*` `asyncmy==0.2.*`

**Endpoints (read-only)**
```
GET  /reference/sites
GET  /reference/programs
GET  /reference/staffed-beds?schedule=Sched-A
GET  /reference/baselines?year=2022
GET  /reference/seasonality?year=2022
GET  /reference/staffing-factors              # may be empty
POST /scenarios/compute                       # returns KPIs + by-site array
```

**Response shape**  
Lists return `{{ "data": [...], "meta": {{ "count": "<int>" }} }}`.  
`/scenarios/compute` returns: `{{"kpis": {{}}, "bySite": []}}` with `fte: null` when factors absent.

**Run locally (non-invasive)**
```bash
# leave existing workflow untouched; run API separately
python -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## 5) Tests (new files only)
**Unit**: `tests/test_services_compute.py` for formulas + guards.  
**Contract**: `tests/test_api_contract.py` mocks DB and validates DTOs.  
**Smoke** (after schema/seed):
```bash
curl -sf http://localhost:8080/reference/seasonality?year=2022 >/dev/null
curl -sf -X POST http://localhost:8080/scenarios/compute \
  -H "content-type: application/json" \
  -d '{{"sites":[1,2,3],"programId":1,"baselineYear":2022,"horizonYears":3,"params":{{"occupancyTarget":0.90,"losDelta":-0.03,"alcTarget":0.12,"growthPct":0.02,"scheduleCode":"Sched-A","seasonality":true}}}}' >/dev/null
echo OK
```

---

## 6) Non‑breaking integration points (optional)
- **setup.py**: after applying `schema.sql`, also run `schema_ext.sql` and (optionally) `seed_ext.sql`.  
- **load_data_mysql.sh**: optionally add a line to run `schema_ext.sql`.  
- **README.md**: add a short “Extensions” section; leave the existing Quick Start intact.

---

## 7) Definition of Done
- New tables exist and are populated (either via `seed_ext.sql` or CSVs + `load_refs.py`).  
- `/reference/*` returns data; `/scenarios/compute` returns KPIs and per‑site rows.  
- No existing file or target has been removed or renamed; original generate/load flows still run unchanged.

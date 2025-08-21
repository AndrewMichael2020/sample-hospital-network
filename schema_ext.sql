-- EXTENSION: Additional tables for FTE and seasonality support
-- This file extends the existing schema.sql with new reference tables
-- Safe to re-run due to IF NOT EXISTS checks

USE lm_synth;

-- EXTENSION: staffed beds schedule (selectable in UI as "Sched-A")
CREATE TABLE IF NOT EXISTS staffed_beds_schedule (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  site_id INT NOT NULL,
  program_id INT NOT NULL,
  schedule_code VARCHAR(32) NOT NULL, -- e.g., 'Sched-A'
  staffed_beds INT NOT NULL,
  UNIQUE KEY uq_sched (site_id, program_id, schedule_code),
  KEY idx_sched_site_prog (site_id, program_id)
) ENGINE=InnoDB;

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
) ENGINE=InnoDB;

-- EXTENSION: seasonality multipliers (month-level; global row via NULL site/program)
CREATE TABLE IF NOT EXISTS seasonality_monthly (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  site_id INT NULL,
  program_id INT NULL,
  month TINYINT NOT NULL CHECK (month BETWEEN 1 AND 12),
  multiplier DECIMAL(6,4) NOT NULL DEFAULT 1.0000,
  UNIQUE KEY uq_season (COALESCE(site_id, -1), COALESCE(program_id, -1), month),
  KEY idx_season_site_prog_month (site_id, program_id, month)
) ENGINE=InnoDB;

-- EXTENSION: staffing factors (optional; enables Nursing FTE calc)
CREATE TABLE IF NOT EXISTS staffing_factors (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  program_id INT NOT NULL,
  subprogram_id INT NULL,
  hppd DECIMAL(6,3) NOT NULL,                 -- hours per patient day
  annual_hours_per_fte INT NOT NULL DEFAULT 1950,
  productivity_factor DECIMAL(6,3) NOT NULL DEFAULT 0.90,
  UNIQUE KEY uq_staffing (program_id, COALESCE(subprogram_id, -1))
) ENGINE=InnoDB;
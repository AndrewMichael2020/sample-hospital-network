-- MySQL DDL for Lower Mainland Healthcare Synthetic Data
-- Creates database schema for sample hospital network data

-- Create database
CREATE DATABASE IF NOT EXISTS lm_synth CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE lm_synth;

-- Create app user (run as root)
-- CREATE USER IF NOT EXISTS 'lm_app'@'%' IDENTIFIED WITH mysql_native_password BY 'hospital_demo_2024';
-- GRANT ALL PRIVILEGES ON lm_synth.* TO 'lm_app'@'%';
-- FLUSH PRIVILEGES;

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
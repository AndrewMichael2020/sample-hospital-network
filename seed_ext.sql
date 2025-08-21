-- EXTENSION: Seed data for new reference tables
-- This file provides initial seed data for the extended schema

USE lm_synth;

-- Seed staffed beds schedule data
INSERT INTO staffed_beds_schedule (site_id, program_id, schedule_code, staffed_beds)
VALUES 
(1,1,'Sched-A',80),(2,1,'Sched-A',70),(3,1,'Sched-A',62),
(4,1,'Sched-A',55),(5,1,'Sched-A',48),(6,1,'Sched-A',40),
(7,1,'Sched-A',75),(8,1,'Sched-A',50),(9,1,'Sched-A',60),
(10,1,'Sched-A',45),(11,1,'Sched-A',35),(12,1,'Sched-A',65),
-- Surgery beds
(1,2,'Sched-A',30),(2,2,'Sched-A',25),(3,2,'Sched-A',22),
(4,2,'Sched-A',18),(5,2,'Sched-A',15),(6,2,'Sched-A',12),
-- Critical Care beds  
(1,4,'Sched-A',16),(2,4,'Sched-A',12),(3,4,'Sched-A',10),
(7,4,'Sched-A',14),(8,4,'Sched-A',8),(9,4,'Sched-A',12)
ON DUPLICATE KEY UPDATE staffed_beds=VALUES(staffed_beds);

-- Seed clinical baseline data
INSERT INTO clinical_baseline (site_id, program_id, baseline_year, los_base_days, alc_rate)
VALUES 
-- Medicine baselines
(1,1,2022,6.0,0.12),(2,1,2022,5.8,0.11),(3,1,2022,5.6,0.10),
(4,1,2022,6.2,0.13),(5,1,2022,5.9,0.12),(6,1,2022,6.1,0.14),
(7,1,2022,5.7,0.11),(8,1,2022,6.3,0.15),(9,1,2022,5.5,0.09),
(10,1,2022,5.8,0.12),(11,1,2022,6.0,0.13),(12,1,2022,5.9,0.11),
-- Surgery baselines
(1,2,2022,4.2,0.08),(2,2,2022,4.1,0.07),(3,2,2022,4.3,0.08),
(4,2,2022,4.5,0.09),(5,2,2022,4.0,0.07),(6,2,2022,4.4,0.08),
-- Critical Care baselines  
(1,4,2022,8.5,0.05),(2,4,2022,8.2,0.06),(3,4,2022,8.8,0.04),
(7,4,2022,8.3,0.05),(8,4,2022,8.6,0.05),(9,4,2022,8.1,0.06)
ON DUPLICATE KEY UPDATE los_base_days=VALUES(los_base_days), alc_rate=VALUES(alc_rate);

-- Seed seasonality multipliers (global defaults)
INSERT INTO seasonality_monthly (site_id, program_id, month, multiplier)
VALUES 
(NULL,NULL,1,1.00),(NULL,NULL,2,1.00),(NULL,NULL,3,1.02),
(NULL,NULL,4,1.01),(NULL,NULL,5,1.00),(NULL,NULL,6,1.00),
(NULL,NULL,7,0.98),(NULL,NULL,8,0.98),(NULL,NULL,9,1.01),
(NULL,NULL,10,1.02),(NULL,NULL,11,1.03),(NULL,NULL,12,1.04)
ON DUPLICATE KEY UPDATE multiplier=VALUES(multiplier);

-- Seed staffing factors for common programs
INSERT INTO staffing_factors (program_id, subprogram_id, hppd, annual_hours_per_fte, productivity_factor)
VALUES 
-- Medicine programs
(1,NULL,6.5,1950,0.92),
-- Surgery programs  
(2,NULL,5.8,1950,0.90),
-- Critical Care programs
(4,NULL,12.5,1950,0.95),
-- Emergency programs
(6,NULL,4.2,1950,0.88)
ON DUPLICATE KEY UPDATE hppd=VALUES(hppd), annual_hours_per_fte=VALUES(annual_hours_per_fte), productivity_factor=VALUES(productivity_factor);
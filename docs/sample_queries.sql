-- Sample SQL Queries for Synthetic Healthcare Database
-- These queries demonstrate common healthcare analytics patterns

-- ==================================================
-- PATIENT DEMOGRAPHICS AND POPULATION ANALYSIS
-- ==================================================

-- 1. Patient count by age group
SELECT 
    CASE 
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 1 THEN 'Infant (0-1)'
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 5 THEN 'Preschool (1-4)'
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 13 THEN 'Child (5-12)'
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 18 THEN 'Adolescent (13-17)'
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 65 THEN 'Adult (18-64)'
        WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 85 THEN 'Senior (65-84)'
        ELSE 'Elderly (85+)'
    END AS age_group,
    COUNT(*) as patient_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM patients), 2) as percentage
FROM patients 
GROUP BY age_group
ORDER BY MIN(TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()));

-- 2. Gender distribution by Local Health Authority
SELECT 
    l.lha_name,
    p.gender,
    COUNT(*) as patient_count
FROM patients p
JOIN dim_lha l ON p.lha_id = l.lha_id
GROUP BY l.lha_id, l.lha_name, p.gender
ORDER BY l.lha_name, p.gender;

-- 3. Population density by facility catchment area
SELECT 
    s.site_name,
    s.site_code,
    COUNT(DISTINCT p.patient_id) as catchment_population,
    s.acute_beds,
    ROUND(COUNT(DISTINCT p.patient_id) / NULLIF(s.acute_beds, 0), 0) as population_per_bed
FROM dim_site s
LEFT JOIN patients p ON s.site_id = p.facility_home
GROUP BY s.site_id, s.site_name, s.site_code, s.acute_beds
ORDER BY population_per_bed DESC;

-- ==================================================
-- EMERGENCY DEPARTMENT ANALYTICS
-- ==================================================

-- 4. ED volume by facility and month
SELECT 
    s.site_name,
    YEAR(e.arrive_ts) as year,
    MONTH(e.arrive_ts) as month,
    COUNT(*) as ed_visits,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, e.arrive_ts, e.depart_ts)), 0) as avg_los_minutes
FROM ed_encounters e
JOIN dim_site s ON e.facility_id = s.site_id
GROUP BY s.site_id, s.site_name, YEAR(e.arrive_ts), MONTH(e.arrive_ts)
ORDER BY s.site_name, year, month;

-- 5. ED acuity distribution
SELECT 
    acuity_level,
    COUNT(*) as visit_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ed_encounters), 2) as percentage,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, arrive_ts, depart_ts)), 0) as avg_los_minutes
FROM ed_encounters
GROUP BY acuity_level
ORDER BY acuity_level;

-- 6. ED discharge disposition patterns
SELECT 
    discharge_disposition,
    COUNT(*) as visit_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ed_encounters), 2) as percentage
FROM ed_encounters
GROUP BY discharge_disposition
ORDER BY visit_count DESC;

-- 7. Busiest ED hours (utilization patterns)
SELECT 
    HOUR(arrive_ts) as hour_of_day,
    COUNT(*) as arrivals,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, arrive_ts, depart_ts)), 0) as avg_los_minutes
FROM ed_encounters
GROUP BY HOUR(arrive_ts)
ORDER BY hour_of_day;

-- ==================================================
-- INPATIENT ANALYTICS
-- ==================================================

-- 8. Average length of stay by program
SELECT 
    p.program_name,
    COUNT(*) as admissions,
    ROUND(AVG(ip.los_days), 2) as avg_los_days,
    ROUND(STDDEV(ip.los_days), 2) as std_los_days,
    MIN(ip.los_days) as min_los,
    MAX(ip.los_days) as max_los
FROM dim_program p
JOIN ip_stays ip ON p.program_id = ip.program_id
GROUP BY p.program_id, p.program_name
ORDER BY avg_los_days DESC;

-- 9. Inpatient volume and capacity utilization
SELECT 
    s.site_name,
    COUNT(*) as total_admissions,
    ROUND(SUM(ip.los_days), 0) as total_patient_days,
    ROUND(AVG(ip.los_days), 2) as avg_los,
    s.acute_beds,
    ROUND(SUM(ip.los_days) / (s.acute_beds * 365), 3) as occupancy_rate_estimate
FROM ip_stays ip
JOIN dim_site s ON ip.facility_id = s.site_id
GROUP BY s.site_id, s.site_name, s.acute_beds
ORDER BY total_patient_days DESC;

-- 10. ALC (Alternate Level of Care) analysis
SELECT 
    p.program_name,
    COUNT(*) as total_stays,
    SUM(CASE WHEN ip.is_alc THEN 1 ELSE 0 END) as alc_stays,
    ROUND(SUM(CASE WHEN ip.is_alc THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as alc_percentage,
    ROUND(AVG(CASE WHEN ip.is_alc THEN ip.los_days END), 2) as avg_alc_los
FROM ip_stays ip
JOIN dim_program p ON ip.program_id = p.program_id
GROUP BY p.program_id, p.program_name
HAVING alc_stays > 0
ORDER BY alc_percentage DESC;

-- ==================================================
-- PATIENT JOURNEY ANALYSIS
-- ==================================================

-- 11. Patients with both ED and IP encounters
SELECT 
    COUNT(DISTINCT p.patient_id) as patients_with_both,
    ROUND(COUNT(DISTINCT p.patient_id) * 100.0 / (SELECT COUNT(*) FROM patients), 2) as percentage_of_population
FROM patients p
WHERE EXISTS (
    SELECT 1 FROM ed_encounters e WHERE e.patient_id = p.patient_id
) AND EXISTS (
    SELECT 1 FROM ip_stays ip WHERE ip.patient_id = p.patient_id
);

-- 12. ED to admission conversion rates
SELECT 
    s.site_name,
    COUNT(e.encounter_id) as total_ed_visits,
    COUNT(CASE WHEN e.discharge_disposition = 'Admitted' THEN 1 END) as admissions_from_ed,
    ROUND(COUNT(CASE WHEN e.discharge_disposition = 'Admitted' THEN 1 END) * 100.0 / COUNT(e.encounter_id), 2) as admission_rate
FROM ed_encounters e
JOIN dim_site s ON e.facility_id = s.site_id
GROUP BY s.site_id, s.site_name
ORDER BY admission_rate DESC;

-- 13. Most active patients (frequent users)
SELECT 
    p.patient_id,
    TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) as age,
    p.gender,
    l.lha_name,
    COALESCE(ed_count.visits, 0) as ed_visits,
    COALESCE(ip_count.stays, 0) as ip_stays,
    (COALESCE(ed_count.visits, 0) + COALESCE(ip_count.stays, 0)) as total_encounters
FROM patients p
JOIN dim_lha l ON p.lha_id = l.lha_id
LEFT JOIN (
    SELECT patient_id, COUNT(*) as visits
    FROM ed_encounters
    GROUP BY patient_id
) ed_count ON p.patient_id = ed_count.patient_id
LEFT JOIN (
    SELECT patient_id, COUNT(*) as stays
    FROM ip_stays
    GROUP BY patient_id
) ip_count ON p.patient_id = ip_count.patient_id
WHERE (COALESCE(ed_count.visits, 0) + COALESCE(ip_count.stays, 0)) >= 5
ORDER BY total_encounters DESC
LIMIT 20;

-- ==================================================
-- FACILITY AND SERVICE ANALYSIS
-- ==================================================

-- 14. Service complexity by facility type
SELECT 
    CASE 
        WHEN s.acute_beds >= 300 THEN 'Large Hospital (300+ beds)'
        WHEN s.acute_beds >= 100 THEN 'Medium Hospital (100-299 beds)'
        WHEN s.acute_beds >= 25 THEN 'Small Hospital (25-99 beds)'
        ELSE 'Community Hospital (<25 beds)'
    END as facility_size,
    COUNT(DISTINCT s.site_id) as facility_count,
    COUNT(DISTINCT ip.program_id) as programs_offered,
    ROUND(AVG(s.acute_beds), 0) as avg_beds,
    SUM(COALESCE(ed_count.visits, 0)) as total_ed_visits,
    SUM(COALESCE(ip_count.stays, 0)) as total_admissions
FROM dim_site s
LEFT JOIN ip_stays ip ON s.site_id = ip.facility_id
LEFT JOIN (
    SELECT facility_id, COUNT(*) as visits
    FROM ed_encounters
    GROUP BY facility_id
) ed_count ON s.site_id = ed_count.facility_id
LEFT JOIN (
    SELECT facility_id, COUNT(*) as stays
    FROM ip_stays
    GROUP BY facility_id
) ip_count ON s.site_id = ip_count.facility_id
GROUP BY facility_size
ORDER BY avg_beds;

-- 15. Program utilization across the health system
SELECT 
    p.program_name,
    COUNT(DISTINCT ip.facility_id) as facilities_offering,
    COUNT(*) as total_stays,
    ROUND(AVG(ip.los_days), 2) as avg_los,
    SUM(ip.los_days) as total_patient_days
FROM dim_program p
JOIN ip_stays ip ON p.program_id = ip.program_id
GROUP BY p.program_id, p.program_name
ORDER BY total_patient_days DESC;

-- ==================================================
-- QUALITY AND PERFORMANCE INDICATORS
-- ==================================================

-- 16. Readmission analysis (simplified - same program within 30 days)
WITH readmissions AS (
    SELECT 
        ip1.patient_id,
        ip1.admit_ts as first_admit,
        ip1.discharge_ts as first_discharge,
        ip2.admit_ts as second_admit,
        ip1.program_id,
        DATEDIFF(ip2.admit_ts, ip1.discharge_ts) as days_between
    FROM ip_stays ip1
    JOIN ip_stays ip2 ON ip1.patient_id = ip2.patient_id 
        AND ip1.program_id = ip2.program_id
        AND ip2.admit_ts > ip1.discharge_ts
        AND DATEDIFF(ip2.admit_ts, ip1.discharge_ts) <= 30
)
SELECT 
    p.program_name,
    COUNT(DISTINCT ip.patient_id) as total_discharges,
    COUNT(DISTINCT r.patient_id) as patients_with_readmissions,
    ROUND(COUNT(DISTINCT r.patient_id) * 100.0 / COUNT(DISTINCT ip.patient_id), 2) as readmission_rate
FROM ip_stays ip
JOIN dim_program p ON ip.program_id = p.program_id
LEFT JOIN readmissions r ON ip.patient_id = r.patient_id AND ip.program_id = r.program_id
GROUP BY p.program_id, p.program_name
HAVING total_discharges >= 10
ORDER BY readmission_rate DESC;

-- 17. System-wide key performance indicators
SELECT 
    'Total Patients' as metric,
    COUNT(*) as value,
    'patients' as unit
FROM patients

UNION ALL

SELECT 
    'Total ED Visits' as metric,
    COUNT(*) as value,
    'visits' as unit
FROM ed_encounters

UNION ALL

SELECT 
    'Total Admissions' as metric,
    COUNT(*) as value,
    'admissions' as unit
FROM ip_stays

UNION ALL

SELECT 
    'Average ED LOS' as metric,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, arrive_ts, depart_ts)), 0) as value,
    'minutes' as unit
FROM ed_encounters

UNION ALL

SELECT 
    'Average Inpatient LOS' as metric,
    ROUND(AVG(los_days), 2) as value,
    'days' as unit
FROM ip_stays

UNION ALL

SELECT 
    'ALC Rate' as metric,
    ROUND(SUM(CASE WHEN is_alc THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as value,
    'percent' as unit
FROM ip_stays;

-- ==================================================
-- DATA VALIDATION QUERIES
-- ==================================================

-- 18. Data integrity checks
SELECT 'Orphaned ED encounters' as check_name, COUNT(*) as count
FROM ed_encounters e
LEFT JOIN patients p ON e.patient_id = p.patient_id
WHERE p.patient_id IS NULL

UNION ALL

SELECT 'Orphaned IP stays', COUNT(*)
FROM ip_stays ip
LEFT JOIN patients p ON ip.patient_id = p.patient_id
WHERE p.patient_id IS NULL

UNION ALL

SELECT 'Invalid facility references in ED', COUNT(*)
FROM ed_encounters e
LEFT JOIN dim_site s ON e.facility_id = s.site_id
WHERE s.site_id IS NULL

UNION ALL

SELECT 'Invalid program references in IP', COUNT(*)
FROM ip_stays ip
LEFT JOIN dim_program p ON ip.program_id = p.program_id
WHERE p.program_id IS NULL

UNION ALL

SELECT 'Future birth dates', COUNT(*)
FROM patients
WHERE date_of_birth > CURDATE()

UNION ALL

SELECT 'Negative length of stay', COUNT(*)
FROM ip_stays
WHERE los_days < 0;
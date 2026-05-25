-- ============================================================
-- NEET Paper Leak Forensic Database — 12 Analytical SQL Queries
-- Each query rated for statistical validity
-- Run against: neet_forensic.db (SQLite3)
-- ============================================================

-- ============================================================
-- QUERY 1: Integrity Score Trend with 3-Year Rolling Average
-- Validity: ✅ Descriptive statistics, fully valid
-- Purpose: Shows how exam integrity has changed over 21 years
-- ============================================================
SELECT
    year,
    exam_name,
    conducting_body,
    integrity_status,
    CASE integrity_status
        WHEN 'Clean' THEN 4
        WHEN 'Minor' THEN 3
        WHEN 'Major' THEN 1
        WHEN 'Cancelled' THEN 0
    END AS integrity_score,
    ROUND(AVG(CASE integrity_status
        WHEN 'Clean' THEN 4
        WHEN 'Minor' THEN 3
        WHEN 'Major' THEN 1
        WHEN 'Cancelled' THEN 0
    END) OVER (ORDER BY year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3yr_avg,
    candidates_appeared,
    candidates_affected
FROM exam_timeline
ORDER BY year;


-- ============================================================
-- QUERY 2: Affected Population as Percentage of Total
-- Validity: ✅ Ratio analysis, fully valid
-- Purpose: Shows impact severity normalized by exam size
-- ============================================================
SELECT
    year,
    candidates_appeared,
    candidates_affected,
    ROUND(100.0 * candidates_affected / NULLIF(candidates_appeared, 0), 2) AS affected_pct,
    integrity_status,
    breach_type
FROM exam_timeline
WHERE candidates_affected > 0
ORDER BY affected_pct DESC;


-- ============================================================
-- QUERY 3: State Investigation Frequency Ranking
-- Validity: ✅ Factual count from CBI/police records
-- Purpose: Which states are most frequently involved in investigations?
-- ============================================================
SELECT
    state,
    state_code,
    investigation_involvement_count,
    investigation_years,
    medical_colleges_total,
    mbbs_seats_total,
    neet_exam_centers_2024,
    CASE
        WHEN investigation_involvement_count >= 4 THEN '🔴 Critical'
        WHEN investigation_involvement_count >= 2 THEN '🟠 High'
        WHEN investigation_involvement_count = 1 THEN '🟡 Moderate'
        ELSE '🟢 Low'
    END AS risk_level
FROM state_infrastructure
WHERE investigation_involvement_count > 0
ORDER BY investigation_involvement_count DESC;


-- ============================================================
-- QUERY 4: CBSE Era vs NTA Era — Full Comparison
-- Validity: ✅ Two-group comparison with clear denominators
-- Purpose: Has exam integrity improved or worsened under NTA?
-- ============================================================
SELECT * FROM v_era_comparison;

-- Detailed breakdown:
SELECT
    conducting_body,
    year,
    integrity_status,
    candidates_appeared,
    candidates_affected,
    arrests_made
FROM exam_timeline
ORDER BY conducting_body, year;


-- ============================================================
-- QUERY 5: Breach Escalation Analysis — Is It Getting Worse?
-- Validity: ✅ Ordinal trend analysis
-- Purpose: Severity-weighted trend over time
-- ============================================================
SELECT
    year,
    integrity_status,
    CASE integrity_status
        WHEN 'Clean' THEN 0
        WHEN 'Minor' THEN 1
        WHEN 'Major' THEN 3
        WHEN 'Cancelled' THEN 5
    END AS severity_weight,
    arrests_made,
    candidates_affected,
    -- Cumulative severity
    SUM(CASE integrity_status
        WHEN 'Clean' THEN 0
        WHEN 'Minor' THEN 1
        WHEN 'Major' THEN 3
        WHEN 'Cancelled' THEN 5
    END) OVER (ORDER BY year) AS cumulative_severity
FROM exam_timeline
ORDER BY year;


-- ============================================================
-- QUERY 6: Financial Impact Calculator (Per Disrupted Year)
-- Validity: ⚠️ Estimate — formula and assumptions documented
-- Purpose: Economic cost of each exam disruption
-- NOTE: Uses avg_coaching_cost from student_impact table
-- ============================================================
SELECT
    e.year,
    e.integrity_status,
    e.candidates_affected,
    s.avg_coaching_cost_lakh,
    ROUND(e.candidates_affected * s.avg_coaching_cost_lakh / 100.0, 0) AS direct_cost_crore_est,
    ROUND(e.candidates_affected * (s.avg_coaching_cost_lakh + 3.0) / 100.0, 0) AS total_cost_with_opportunity_crore_est,
    '⚠️ ESTIMATE: coaching_cost × affected + opportunity_cost (₹3L/yr)' AS methodology_note
FROM exam_timeline e
JOIN student_impact s ON e.year = s.year
WHERE e.candidates_affected > 0
ORDER BY total_cost_with_opportunity_crore_est DESC;


-- ============================================================
-- QUERY 7: Gender Impact in Disrupted vs Clean Years
-- Validity: ✅ Before/after comparison with clear metrics
-- Purpose: Do disruptions disproportionately affect female candidates?
-- ============================================================
SELECT
    CASE
        WHEN e.integrity_status IN ('Major', 'Cancelled') THEN 'Disrupted Year'
        ELSE 'Normal Year'
    END AS year_type,
    COUNT(*) AS year_count,
    ROUND(AVG(s.female_candidate_pct), 1) AS avg_female_pct,
    ROUND(AVG(s.sc_st_obc_pct), 1) AS avg_sc_st_obc_pct
FROM exam_timeline e
JOIN student_impact s ON e.year = s.year
GROUP BY year_type;


-- ============================================================
-- QUERY 8: Suicide Trend Correlation with Exam Disruptions
-- Validity: ⚠️ Correlation analysis — does NOT imply causation
-- Purpose: Do exam-related suicides spike in years of disruption?
-- ============================================================
SELECT
    s.year,
    s.student_suicides_national_exam_related,
    s.kota_student_suicides,
    e.integrity_status,
    CASE
        WHEN e.integrity_status IN ('Major', 'Cancelled') THEN 'Disrupted'
        ELSE 'Normal'
    END AS disruption_flag,
    LAG(s.student_suicides_national_exam_related) OVER (ORDER BY s.year) AS prev_year_suicides,
    s.student_suicides_national_exam_related - LAG(s.student_suicides_national_exam_related) OVER (ORDER BY s.year) AS yoy_change
FROM student_impact s
JOIN exam_timeline e ON s.year = e.year
WHERE s.student_suicides_national_exam_related IS NOT NULL
ORDER BY s.year;


-- ============================================================
-- QUERY 9: Doctor Pipeline Delay Impact
-- Validity: ⚠️ Estimate — assumptions documented
-- Purpose: How many doctors does each cancellation delay?
-- ============================================================
SELECT
    year,
    integrity_status,
    candidates_qualified,
    CASE
        WHEN integrity_status = 'Cancelled' THEN candidates_qualified
        WHEN integrity_status = 'Major' THEN ROUND(candidates_qualified * 0.05)
        ELSE 0
    END AS doctors_delayed_est,
    '⚠️ Assumes qualified candidates in cancelled years are delayed 1 year; Major years: 5% disruption' AS methodology
FROM exam_timeline
WHERE integrity_status IN ('Major', 'Cancelled')
ORDER BY year;


-- ============================================================
-- QUERY 10: Modus Operandi Evolution
-- Validity: ✅ Factual classification from CBI records
-- Purpose: How have cheating methods evolved?
-- ============================================================
SELECT
    year,
    event_title,
    severity,
    modus_operandi,
    arrests,
    states_implicated,
    CASE
        WHEN year <= 2017 THEN 'Era 1: Physical (proxy/bluetooth)'
        WHEN year <= 2022 THEN 'Era 2: Document (OMR/paper theft)'
        ELSE 'Era 3: Digital (Telegram/pipeline)'
    END AS modus_era
FROM breach_events
ORDER BY year;


-- ============================================================
-- QUERY 11: State Healthcare Vulnerability Index
-- Validity: ✅ Composite index from verified metrics
-- Purpose: Which states are most harmed by exam disruptions?
-- ============================================================
SELECT
    state,
    state_code,
    phc_doctor_vacancy_pct,
    CAST(SUBSTR(doctor_patient_ratio, 3) AS INTEGER) AS patients_per_doctor,
    mbbs_seats_total,
    investigation_involvement_count,
    -- Vulnerability = high vacancy + high ratio + low seats + investigation involvement
    ROUND(
        (phc_doctor_vacancy_pct / 100.0) * 0.3 +
        (CAST(SUBSTR(doctor_patient_ratio, 3) AS INTEGER) / 5200.0) * 0.3 +
        (1.0 - mbbs_seats_total / 10800.0) * 0.2 +
        (investigation_involvement_count / 5.0) * 0.2
    , 3) AS vulnerability_score
FROM state_infrastructure
ORDER BY vulnerability_score DESC
LIMIT 15;


-- ============================================================
-- QUERY 12: Year-over-Year Candidate Growth vs Disruption
-- Validity: ✅ Time series analysis
-- Purpose: Does candidate count drop after disrupted years?
-- ============================================================
SELECT
    year,
    candidates_appeared,
    LAG(candidates_appeared) OVER (ORDER BY year) AS prev_year,
    candidates_appeared - LAG(candidates_appeared) OVER (ORDER BY year) AS absolute_change,
    ROUND(100.0 * (candidates_appeared - LAG(candidates_appeared) OVER (ORDER BY year)) / NULLIF(LAG(candidates_appeared) OVER (ORDER BY year), 0), 1) AS pct_change,
    integrity_status,
    LAG(integrity_status) OVER (ORDER BY year) AS prev_year_status,
    CASE
        WHEN LAG(integrity_status) OVER (ORDER BY year) IN ('Major', 'Cancelled')
            AND (candidates_appeared - LAG(candidates_appeared) OVER (ORDER BY year)) < 0
        THEN '⚠️ Post-disruption decline'
        WHEN LAG(integrity_status) OVER (ORDER BY year) IN ('Major', 'Cancelled')
            AND (candidates_appeared - LAG(candidates_appeared) OVER (ORDER BY year)) >= 0
        THEN 'Resilient growth despite disruption'
        ELSE 'Normal'
    END AS pattern
FROM exam_timeline
ORDER BY year;

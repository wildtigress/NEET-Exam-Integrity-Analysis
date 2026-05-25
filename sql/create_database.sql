-- ============================================================
-- NEET Paper Leak Forensic Database — Schema
-- SQLite3 compatible
-- Source: All data from NTA, NCRB, CBI, Supreme Court, Parliamentary Committee
-- ============================================================

-- Drop existing tables if re-running
DROP TABLE IF EXISTS exam_timeline;
DROP TABLE IF EXISTS breach_events;
DROP TABLE IF EXISTS student_impact;
DROP TABLE IF EXISTS state_infrastructure;
DROP TABLE IF EXISTS exam_benchmarking;

-- ============================================================
-- TABLE 1: exam_timeline — 21 years of AIPMT/NEET conduct
-- ============================================================
CREATE TABLE exam_timeline (
    year INTEGER PRIMARY KEY,
    exam_name TEXT NOT NULL CHECK(exam_name IN ('AIPMT', 'NEET-UG')),
    conducting_body TEXT NOT NULL CHECK(conducting_body IN ('CBSE', 'NTA')),
    integrity_status TEXT NOT NULL CHECK(integrity_status IN ('Clean', 'Minor', 'Major', 'Cancelled')),
    candidates_registered INTEGER,
    candidates_appeared INTEGER,
    candidates_qualified INTEGER,
    candidates_affected INTEGER DEFAULT 0,
    breach_type TEXT DEFAULT 'None',
    states_involved TEXT,  -- semicolon-separated state codes
    arrests_made INTEGER DEFAULT 0,
    legal_outcome TEXT,
    corrected_from_v1 BOOLEAN DEFAULT FALSE,
    source TEXT NOT NULL
);

-- ============================================================
-- TABLE 2: breach_events — detailed confirmed incidents
-- ============================================================
CREATE TABLE breach_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    event_title TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('Minor', 'Major', 'Cancelled')),
    description TEXT NOT NULL,
    states_implicated TEXT,
    modus_operandi TEXT,
    arrests INTEGER DEFAULT 0,
    legal_outcome TEXT,
    amount_charged_lakh TEXT,
    source TEXT NOT NULL,
    FOREIGN KEY (year) REFERENCES exam_timeline(year)
);

-- ============================================================
-- TABLE 3: student_impact — annual human cost metrics
-- ============================================================
CREATE TABLE student_impact (
    year INTEGER PRIMARY KEY,
    student_suicides_national_exam_related INTEGER,
    kota_student_suicides INTEGER,
    coaching_industry_revenue_cr REAL,
    avg_coaching_cost_lakh REAL,
    female_candidate_pct REAL,
    sc_st_obc_pct REAL,
    dropout_after_failure_pct REAL,
    mental_health_helpline_calls INTEGER,
    source_suicides TEXT,
    source_coaching TEXT,
    FOREIGN KEY (year) REFERENCES exam_timeline(year)
);

-- ============================================================
-- TABLE 4: state_infrastructure — medical ecosystem per state
-- ============================================================
CREATE TABLE state_infrastructure (
    state TEXT PRIMARY KEY,
    state_code TEXT UNIQUE NOT NULL,
    medical_colleges_total INTEGER,
    govt_medical_colleges INTEGER,
    pvt_medical_colleges INTEGER,
    mbbs_seats_total INTEGER,
    neet_exam_centers_2024 INTEGER,
    doctor_patient_ratio TEXT,
    phc_doctor_vacancy_pct REAL,
    investigation_involvement_count INTEGER DEFAULT 0,
    investigation_years TEXT,
    source TEXT NOT NULL
);

-- ============================================================
-- TABLE 5: exam_benchmarking — NEET vs global exams
-- ============================================================
CREATE TABLE exam_benchmarking (
    exam_name TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    mode TEXT NOT NULL,
    annual_candidates INTEGER,
    confirmed_leak_incidents INTEGER DEFAULT 0,
    cancellations INTEGER DEFAULT 0,
    exam_centers INTEGER,
    security_score_out_of_10 INTEGER,
    key_security_feature TEXT,
    conducting_body TEXT,
    source TEXT NOT NULL
);

-- ============================================================
-- INDEXES for query performance
-- ============================================================
CREATE INDEX idx_timeline_status ON exam_timeline(integrity_status);
CREATE INDEX idx_timeline_body ON exam_timeline(conducting_body);
CREATE INDEX idx_breach_year ON breach_events(year);
CREATE INDEX idx_breach_severity ON breach_events(severity);
CREATE INDEX idx_state_investigation ON state_infrastructure(investigation_involvement_count);
CREATE INDEX idx_impact_year ON student_impact(year);

-- ============================================================
-- VIEWS for common analysis patterns
-- ============================================================

-- View: Summary of each era (CBSE vs NTA)
CREATE VIEW v_era_comparison AS
SELECT
    conducting_body AS era,
    COUNT(*) AS total_years,
    SUM(CASE WHEN integrity_status = 'Clean' THEN 1 ELSE 0 END) AS clean_years,
    SUM(CASE WHEN integrity_status = 'Minor' THEN 1 ELSE 0 END) AS minor_years,
    SUM(CASE WHEN integrity_status = 'Major' THEN 1 ELSE 0 END) AS major_years,
    SUM(CASE WHEN integrity_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_years,
    ROUND(100.0 * SUM(CASE WHEN integrity_status = 'Clean' THEN 1 ELSE 0 END) / COUNT(*), 1) AS clean_pct,
    SUM(candidates_affected) AS total_affected,
    SUM(arrests_made) AS total_arrests
FROM exam_timeline
GROUP BY conducting_body;

-- View: State risk ranking
CREATE VIEW v_state_risk_ranking AS
SELECT
    state,
    state_code,
    investigation_involvement_count,
    investigation_years,
    medical_colleges_total,
    mbbs_seats_total,
    phc_doctor_vacancy_pct,
    CASE
        WHEN investigation_involvement_count >= 4 THEN 'Critical'
        WHEN investigation_involvement_count >= 2 THEN 'High'
        WHEN investigation_involvement_count = 1 THEN 'Moderate'
        ELSE 'Low'
    END AS risk_level
FROM state_infrastructure
ORDER BY investigation_involvement_count DESC;

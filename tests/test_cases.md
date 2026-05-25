# NEET Paper Leak Dashboard — 25 Test Cases

## Category 1: Data Integrity (T1–T5)

### T1: Year Completeness
- **Check:** All 21 years (2006–2026) present in exam_timeline
- **SQL:** `SELECT COUNT(DISTINCT year) FROM exam_timeline;` → should return 21
- **Pass/Fail:** [ ]

### T2: No Duplicate Years
- **Check:** No year appears twice
- **SQL:** `SELECT year, COUNT(*) FROM exam_timeline GROUP BY year HAVING COUNT(*) > 1;` → should return 0 rows
- **Pass/Fail:** [ ]

### T3: Positive Candidate Counts
- **Check:** candidates_appeared > 0 for every year
- **SQL:** `SELECT * FROM exam_timeline WHERE candidates_appeared <= 0;` → should return 0 rows
- **Pass/Fail:** [ ]

### T4: Affected ≤ Appeared
- **Check:** candidates_affected never exceeds candidates_appeared
- **SQL:** `SELECT * FROM exam_timeline WHERE candidates_affected > candidates_appeared;` → should return 0 rows
- **Pass/Fail:** [ ]

### T5: Source Citations Present
- **Check:** Every row has a non-empty source
- **SQL:** `SELECT * FROM exam_timeline WHERE source IS NULL OR source = '';` → should return 0 rows
- **Pass/Fail:** [ ]

---

## Category 2: Statistical Validity (T6–T10)

### T6: P-Values in Valid Range
- **Check:** All p-values from Python tests are between 0 and 1
- **How:** Open `python/output/statistical_test_results.csv`, check p_value column
- **Pass/Fail:** [ ]

### T7: Sample Size Adequacy
- **Check:** Each statistical test has n ≥ 5 per comparison group
- **How:** CBSE has 13 years, NTA has 8 years — both ≥ 5 ✓
- **Pass/Fail:** [ ]

### T8: Conclusions Match Significance
- **Check:** "REJECT H0" only when p < 0.05; "FAIL TO REJECT H0" only when p ≥ 0.05
- **How:** Cross-check each row in test results CSV
- **Pass/Fail:** [ ]

### T9: No Causal Claims from Correlational Tests
- **Check:** Spearman correlation (T3) does not claim causation in output text
- **How:** Read the Python console output for T3 — should say "correlation" not "causes"
- **Pass/Fail:** [ ]

### T10: Estimates Flagged
- **Check:** Financial calculations (Query 6) explicitly say "ESTIMATE"
- **How:** Open forensic_queries.sql, find Query 6 — check for  flag
- **Pass/Fail:** [ ]

---

## Category 3: Dashboard Accuracy (T11–T15)

### T11: KPI Numbers Match CSV
- **Check:** "Confirmed clean exams" card shows 10/21 (from exam_timeline.csv count)
- **How:** Count manually: 2006-2008, 2009, 2010, 2011, 2012, 2013, 2018, 2020, 2022 = 10 clean
- **Pass/Fail:** [ ]

### T12: Chart Data Matches Source
- **Check:** Bar chart values for "candidates_appeared" match CSV column F
- **How:** Hover over 2024 bar — should show 24,00,000 (24 lakh)
- **Pass/Fail:** [ ]

### T13: All 21 Years in Heatmap
- **Check:** The integrity heatmap shows cells for every year 2006–2026
- **How:** Count cells visually — should be 21
- **Pass/Fail:** [ ]

### T14: Tooltip Content Accuracy
- **Check:** Hovering over 2015 bar shows "Cancelled" + 6.3L affected
- **How:** Hover and read tooltip text
- **Pass/Fail:** [ ]

### T15: Responsive Layout
- **Check:** Dashboard works at 375px width (mobile)
- **How:** Open browser DevTools (F12) → Toggle device toolbar → select iPhone SE
- **Pass/Fail:** [ ]

---

## Category 4: SQL Query Validation (T16–T20)

### T16: Query 1 Row Count
- **Check:** Integrity Score Trend query returns exactly 21 rows
- **How:** Run Query 1 in DB Browser → check row count
- **Pass/Fail:** [ ]

### T17: Investigation Total Cross-Check
- **Check:** Sum of investigation_involvement_count in Query 3 matches actual breach data
- **SQL:** `SELECT SUM(investigation_involvement_count) FROM state_infrastructure;`
- **Cross-check:** Count unique state appearances in breach_events.states_implicated
- **Pass/Fail:** [ ]

### T18: Financial Estimates Flagged
- **Check:** Query 6 output includes methodology_note column with 
- **How:** Run Query 6 → check last column
- **Pass/Fail:** [ ]

### T19: JOIN Integrity
- **Check:** Query 6 (timeline JOIN impact) returns rows only for matching years
- **How:** Run query → verify no NULL year values
- **Pass/Fail:** [ ]

### T20: NULL Handling
- **Check:** Query 8 (suicide trend) correctly excludes years with NULL suicide data
- **How:** Run query → verify no NULL values in suicide column
- **Pass/Fail:** [ ]

---

## Category 5: Ethical/Methodology (T21–T25)

### T21: No Causal Claims
- **Check:** Dashboard text says "correlated with" or "associated with", never "caused by"
- **How:** Ctrl+F search dashboard for "cause" or "proves" — should find 0
- **Pass/Fail:** [ ]

### T22: All Estimates Clearly Labeled
- **Check:** Financial figures (₹50,000 Cr) are marked as "est." or "estimate"
- **How:** Find all ₹ references in dashboard — each should have a qualifier
- **Pass/Fail:** [ ]

### T23: Source Citations on All Data
- **Check:** Every section of the dashboard has a source reference
- **How:** Check footer/source section of dashboard
- **Pass/Fail:** [ ]

### T24: Neutral State Naming
- **Check:** States are described by "investigation involvement" not "guilty" or "corrupt"
- **How:** Read all state-related text in dashboard
- **Pass/Fail:** [ ]

### T25: Limitations Documented
- **Check:** Dashboard or guide mentions data limitations (no NTA microdata, estimates flagged)
- **How:** Check for a limitations section or notes
- **Pass/Fail:** [ ]

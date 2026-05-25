# 🎓 NEET Paper Leak Dashboard — Step-by-Step Learning Guide

> **Learn by doing.** Each step teaches you a real data analyst skill while building this project.
> Total time: ~8-10 hours | Difficulty: Intermediate | Skills covered: 7

---

## 📋 PREREQUISITES (Do This First — 15 min)

### Step 0.1: Set Up Your Project Folder
1. Open File Explorer
2. Navigate to: `C:\Users\SAMIKSHA BARNWAL\.gemini\antigravity\scratch\neet-paper-leak-dashboard`
3. You should see these folders already created: `data/`, `sql/`, `python/`, `guides/`, `tests/`
4. **Skill learned:** Project organization — every data project needs a clean folder structure

### Step 0.2: Install Python (if not already)
1. Open PowerShell and type: `python --version`
2. If not installed, download from https://python.org (check "Add to PATH" during install)
3. Install required libraries:
```powershell
cd "C:\Users\SAMIKSHA BARNWAL\.gemini\antigravity\scratch\neet-paper-leak-dashboard"
pip install pandas numpy scipy matplotlib seaborn requests openpyxl
```
4. **Skill learned:** Environment setup — every analyst needs Python configured

### Step 0.3: Install DB Browser for SQLite
1. Download from: https://sqlitebrowser.org/dl/
2. Install it (free, no signup needed)
3. **Why:** This lets you visually run SQL queries on your database

---

## 🟢 PHASE 1: GOOGLE SHEETS — Data Collection & Cleaning (1.5 hours)

> **Skills:** Data entry, data validation, conditional formatting, pivot tables, VLOOKUP

### Step 1.1: Create a New Google Sheet
1. Go to https://sheets.google.com → Click **Blank spreadsheet**
2. Rename it: `NEET Paper Leak Forensic Dataset`
3. Create **6 tabs** at the bottom: `exam_timeline`, `breach_events`, `student_impact`, `state_infrastructure`, `exam_benchmarking`, `analysis_notes`

### Step 1.2: Import the exam_timeline Data
1. Open the file `data/exam_timeline.csv` in Notepad
2. Copy ALL the content
3. In your Google Sheet tab `exam_timeline`, click cell A1
4. Go to **File → Import → Upload** → drag the CSV file, OR paste and use **Data → Split text to columns**
5. You should see 21 rows of data (years 2006–2026) with 14 columns

**🔍 LEARN BY OBSERVING:**
- Look at the `integrity_status` column — count how many say "Clean" vs "Major" vs "Cancelled"
- Look at `candidates_appeared` — notice how it grew from 2.45 lakh (2006) to 22.7 lakh (2026)
- **Question to ask yourself:** "What pattern do I see in the last 5 years vs first 5 years?"

### Step 1.3: Add Data Validation Rules
1. Select the `integrity_status` column (D2:D22)
2. Go to **Data → Data validation → Add rule**
3. Criteria: **Dropdown from a list** → type: `Clean, Minor, Major, Cancelled`
4. Click **Done**
5. Do the same for `conducting_body` column: dropdown with `CBSE, NTA`

**💡 Why?** Data validation prevents typos. In real datasets, one wrong entry like "clean" vs "Clean" breaks all your analysis.

### Step 1.4: Add Conditional Formatting
1. Select cells D2:D22 (integrity_status column)
2. **Format → Conditional formatting**
3. Add 4 rules:
   - Text is exactly `Clean` → green background (#639922), white text
   - Text is exactly `Minor` → amber background (#BA7517), white text
   - Text is exactly `Major` → red background (#E24B4A), white text
   - Text is exactly `Cancelled` → dark red background (#A32D2D), white text
4. Now you have a visual heatmap right in your spreadsheet!

**💡 Skill learned:** Conditional formatting = instant visual analysis. Real analysts use this to spot patterns before writing a single line of code.

### Step 1.5: Import the Other 4 CSV Files
Repeat steps 1.2 for each file into its respective tab:
- `breach_events.csv` → `breach_events` tab
- `student_impact.csv` → `student_impact` tab  
- `state_infrastructure.csv` → `state_infrastructure` tab
- `exam_benchmarking.csv` → `exam_benchmarking` tab

### Step 1.6: Create Calculated Columns
In the `exam_timeline` tab, add these NEW columns:

**Column O (header: `affected_pct`):**
In cell O2, type this formula and drag down:
```
=IF(G2>0, ROUND(H2/G2*100, 2), 0)
```
This calculates: What % of appeared candidates were affected?

**Column P (header: `severity_score`):**
```
=IF(D2="Clean", 0, IF(D2="Minor", 1, IF(D2="Major", 3, 5)))
```
This converts text status to a number for charting.

**Column Q (header: `era`):**
```
=IF(C2="CBSE", "CBSE Era (2006-2018)", "NTA Era (2019-2026)")
```

**💡 Skill learned:** Calculated columns = deriving new insights from raw data. This is 50% of a data analyst's job.

### Step 1.7: Build a Pivot Table
1. Select ALL data in `exam_timeline` (Ctrl+A)
2. **Insert → Pivot table → New sheet**
3. Set up:
   - Rows: `conducting_body`
   - Columns: `integrity_status`
   - Values: `year` → Summarize by COUNTA (count)
4. **What you should see:**

| | Clean | Minor | Major | Cancelled |
|---|---|---|---|---|
| CBSE | 8 | 4 | 0 | 1 |
| NTA | 2 | 2 | 3 | 1 |

**🔍 KEY INSIGHT:** CBSE had 8/13 clean years (62%). NTA has 2/8 clean years (25%). This is the data telling a story.

### Step 1.8: Create Charts in Google Sheets
1. Go back to `exam_timeline` tab
2. Select columns A (year) and P (severity_score)
3. **Insert → Chart**
4. Change chart type to **Column chart**
5. Title it: "Exam Integrity Score Over 21 Years"
6. Customize colors to match the red/green scheme

**Create a second chart:**
1. Select columns A (year), F (candidates_appeared), H (candidates_affected)
2. Insert → Chart → **Combo chart** (bar + bar)
3. Title: "Candidates Appeared vs Affected"

**💡 Skill learned:** Google Sheets charts are your "quick and dirty" analysis tool. Real analysts use these for internal presentations before building fancy dashboards.

### ✅ PHASE 1 CHECKPOINT
You should now have:
- [ ] A Google Sheet with 6 tabs of real data
- [ ] Data validation on key columns
- [ ] Conditional formatting showing color-coded integrity status
- [ ] 3 calculated columns (affected_pct, severity_score, era)
- [ ] 1 pivot table showing CBSE vs NTA breakdown
- [ ] 2 charts

---

## 🟡 PHASE 2: SQL — Database & Forensic Queries (1.5 hours)

> **Skills:** CREATE TABLE, SELECT, JOIN, GROUP BY, HAVING, window functions, views

### Step 2.1: Create the SQLite Database
1. Open **DB Browser for SQLite**
2. Click **New Database**
3. Save as: `neet-paper-leak-dashboard/data/neet_forensic.db`
4. When it asks to create a table, click **Cancel** (we'll use our SQL file)

### Step 2.2: Run the Schema SQL
1. Click the **Execute SQL** tab in DB Browser
2. Open file: `sql/create_database.sql`
3. Click **Execute All** (▶️ button or F5)
4. You should see "Execution finished without errors"
5. Click **Browse Data** tab — you'll see empty tables

### Step 2.3: Import CSV Data into Tables
For each table:
1. Go to **File → Import → Table from CSV file**
2. Select `data/exam_timeline.csv`
3. Table name: `exam_timeline`
4. Check "Column names in first line"
5. Click OK
6. Repeat for all 5 CSV files

**Verify:** Click Browse Data → select `exam_timeline` → you should see 21 rows

### Step 2.4: Run Your First Forensic Query
Go to **Execute SQL** tab. Type and run:

```sql
-- Query: How many clean years in each era?
SELECT 
    conducting_body,
    COUNT(*) AS total_years,
    SUM(CASE WHEN integrity_status = 'Clean' THEN 1 ELSE 0 END) AS clean_years,
    ROUND(100.0 * SUM(CASE WHEN integrity_status = 'Clean' THEN 1 ELSE 0 END) / COUNT(*), 1) AS clean_pct
FROM exam_timeline
GROUP BY conducting_body;
```

**🔍 What you should see:**
| conducting_body | total_years | clean_years | clean_pct |
|---|---|---|---|
| CBSE | 13 | 8 | 61.5 |
| NTA | 8 | 2 | 25.0 |

**💡 This is the SAME insight as your pivot table — but now in SQL. Real analysts use SQL for larger datasets where Google Sheets can't handle the volume.**

### Step 2.5: Run the 12 Forensic Queries
1. Open `sql/forensic_queries.sql`
2. Run each query ONE AT A TIME (highlight the query → Execute)
3. For EACH query, write down:
   - What question does this query answer?
   - What did the result tell you?
   - Was the result surprising?

**Key queries to pay attention to:**

**Query 3 (State Investigation Frequency):**
```sql
SELECT state, investigation_involvement_count, investigation_years
FROM state_infrastructure 
WHERE investigation_involvement_count > 0
ORDER BY investigation_involvement_count DESC;
```
**Expected result:** Rajasthan (5 investigations) leads, followed by Bihar and Maharashtra.

**Query 5 (Breach Escalation):**
Look at the `cumulative_severity` column — if it's accelerating upward in recent years, breaches are getting worse.

**Query 10 (Modus Operandi Evolution):**
Notice how methods evolved: Physical (bluetooth vests) → Document (OMR/paper theft) → Digital (Telegram leaks). This mirrors real-world crime evolution.

### Step 2.6: Write Your OWN Query
Try writing a query yourself. Here's a challenge:

**Challenge:** "Which years had MORE than 100,000 candidates affected, and what was the breach type?"

```sql
-- Try writing this yourself first, then check below!
```

<details>
<summary>Click to see answer</summary>

```sql
SELECT year, breach_type, candidates_affected, integrity_status
FROM exam_timeline
WHERE candidates_affected > 100000
ORDER BY candidates_affected DESC;
```
</details>

### ✅ PHASE 2 CHECKPOINT
You should now have:
- [ ] A working SQLite database with 5 tables
- [ ] Successfully run all 12 forensic queries
- [ ] Written at least 1 custom query yourself
- [ ] Notes on what each query revealed

---

## 🔵 PHASE 3: PYTHON — Statistical Analysis (1.5 hours)

> **Skills:** pandas, numpy, scipy, matplotlib, sqlite3, hypothesis testing

### Step 3.1: Run the Analysis Script
1. Open PowerShell
2. Navigate to project:
```powershell
cd "C:\Users\SAMIKSHA BARNWAL\.gemini\antigravity\scratch\neet-paper-leak-dashboard"
```
3. Run the analysis:
```powershell
python python/analysis.py
```
4. You should see output for all 5 modules with test results

### Step 3.2: Understand Each Statistical Test
After running, open `python/output/statistical_test_results.csv` and study each row:

| Test | What It Tests | What p < 0.05 Means |
|------|--------------|---------------------|
| Chi-Square GoF | Are integrity categories equally distributed? | No — some categories are over/under-represented |
| Mann-Whitney U | Are disrupted years different in size? | Yes — disrupted years tend to be larger exams |
| Spearman Correlation | Does investigation correlate with doctor shortage? | Would mean states with more investigations also have worse healthcare |
| Fisher's Exact | Are investigation states also big-seat states? | Would mean large states are targeted more |
| Wilcoxon | Do female numbers drop after cancellations? | Would show gender-disproportionate impact |
| Linear Regression | Is severity increasing over time? | Would confirm breaches are escalating |
| Two-Proportion Z | Is CBSE era cleaner than NTA? | Would confirm the era comparison statistically |

**💡 KEY LEARNING:** A p-value < 0.05 means the result is "statistically significant" — there's less than 5% chance it happened by random chance. But **correlation ≠ causation**. Just because two things correlate doesn't mean one causes the other.

### Step 3.3: Examine the Charts
1. Open the `python/output/` folder
2. Look at each PNG chart:
   - `01_integrity_timeline.png` — Do you see the pattern of worsening in recent years?
   - `04_state_investigations.png` — Which state has the tallest bar?
   - `05_correlation_heatmap.png` — Which variables are strongly correlated (dark red/blue)?
   - `06_cbse_vs_nta.png` — Are the boxes different heights?

### Step 3.4: Modify the Script (Learn by Changing)
Open `python/analysis.py` in any text editor and try these modifications:

**Modification 1:** Add a new chart showing coaching industry revenue growth:
```python
# Add this after chart 6 in generate_visualizations():
fig, ax = plt.subplots(figsize=(10, 5))
revenue_data = impact.dropna(subset=['coaching_industry_revenue_cr'])
ax.fill_between(revenue_data['year'], revenue_data['coaching_industry_revenue_cr'], 
                alpha=0.3, color='#7F77DD')
ax.plot(revenue_data['year'], revenue_data['coaching_industry_revenue_cr'], 
        'o-', color='#7F77DD', linewidth=2)
ax.set_title('Coaching Industry Revenue Growth (₹ Crores)', fontweight='bold')
ax.set_xlabel('Year')
ax.set_ylabel('Revenue (₹ Crores)')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "07_coaching_revenue.png", dpi=150)
plt.close()
```

**Modification 2:** Add a new statistical test — is coaching cost correlated with suicides?

**💡 Skill learned:** Real data analysts spend 60% of their time modifying and iterating on code. The ability to tweak existing scripts is more valuable than writing from scratch.

### ✅ PHASE 3 CHECKPOINT
- [ ] Python script ran successfully
- [ ] 6 PNG charts generated in `output/` folder
- [ ] Statistical test results CSV generated
- [ ] You understand what p-value means for at least 3 tests
- [ ] You modified the script and added at least 1 new chart

---

## 🟣 PHASE 4: INTERACTIVE DASHBOARD (2 hours)

> **Skills:** HTML, CSS, JavaScript, Chart.js, data visualization, responsive design

### Step 4.1: Open the Dashboard
1. Navigate to: `neet-paper-leak-dashboard/`
2. Double-click `index.html` to open in your browser
3. You should see the full interactive dashboard

### Step 4.2: Understand the Dashboard Structure
Open `index.html` in VS Code or any editor. Read through the code and identify:

1. **Lines 1-50:** HTML head — Google Font loading, Chart.js library import
2. **Lines ~50-200:** CSS — all the styling (dark theme, glassmorphism, animations)
3. **Lines ~200-500:** HTML body — the dashboard layout with sections
4. **Lines 500+:** JavaScript — data arrays and Chart.js configurations

### Step 4.3: Modify a Chart (Learn by Changing)
Find the `candChart` (Candidates chart) in the JavaScript section. Try:
1. Change a bar color from `#85B7EB` to `#7F77DD`
2. Save the file
3. Refresh the browser
4. See your change!

### Step 4.4: Add Your Own Data Point
Find the data arrays in JavaScript. Notice how they match your CSV files — the dashboard reads from hardcoded arrays (since it's a single HTML file with no server).

Try adding a note to the breach events section describing a finding from your SQL analysis.

### Step 4.5: Test Interactivity
1. **Hover** over any chart bar — you should see a tooltip with exact numbers
2. **Click** on states in the India map — observe what happens
3. **Resize** the browser window — check if the layout adapts (responsive design)
4. **Toggle** dark/light mode if available

**💡 Skill learned:** Interactive dashboards are the "final product" that stakeholders see. Everything you did in Sheets/SQL/Python was preparation for this moment.

### ✅ PHASE 4 CHECKPOINT
- [ ] Dashboard opens correctly in browser
- [ ] All charts render with real data
- [ ] You modified at least one visual element
- [ ] You understand how the data flows from arrays → charts

---

## 🟤 PHASE 5: POWER BI DESKTOP (1 hour)

> **Skills:** Power BI import, DAX measures, report building, filters

### Step 5.1: Download Power BI Desktop (Free)
1. Go to: https://powerbi.microsoft.com/desktop/
2. Download and install (completely free, no Pro needed)

### Step 5.2: Import Your Data
1. Open Power BI Desktop
2. **Get Data → Text/CSV**
3. Import `exam_timeline.csv` → Click **Load**
4. Repeat for all 5 CSV files
5. You should see 5 tables in the right panel

### Step 5.3: Create Relationships
1. Go to **Model** view (left sidebar, 3rd icon)
2. Drag `exam_timeline.year` → `student_impact.year` (creates a relationship)
3. Drag `exam_timeline.year` → `breach_events.year`
4. This lets you cross-filter between tables

### Step 5.4: Create DAX Measures
Click **New Measure** and add:

```
Clean Exam Rate = 
DIVIDE(
    COUNTROWS(FILTER(exam_timeline, exam_timeline[integrity_status] = "Clean")),
    COUNTROWS(exam_timeline)
)
```

```
Total Affected = SUM(exam_timeline[candidates_affected])
```

```
Avg Severity = 
AVERAGEX(
    exam_timeline,
    SWITCH(
        exam_timeline[integrity_status],
        "Clean", 0,
        "Minor", 1,
        "Major", 3,
        "Cancelled", 5
    )
)
```

### Step 5.5: Build Your First Report Page
1. Switch to **Report** view
2. Add a **Card** visual → drag `Total Affected` → format as number
3. Add a **Stacked Bar Chart** → Axis: `year`, Values: `candidates_appeared` and `candidates_affected`
4. Add a **Donut Chart** → Legend: `integrity_status`, Values: Count of `year`
5. Add a **Slicer** → Field: `conducting_body` → Now you can filter CBSE vs NTA!

### Step 5.6: Format Like a Pro
1. Select a chart → Format pane → change colors to match our scheme:
   - Clean: #639922, Minor: #BA7517, Major: #E24B4A, Cancelled: #A32D2D
2. Add a text box with the title: "NEET Paper Leak Forensic Dashboard"
3. Set the page background to dark gray (#1a1a2e)

### Step 5.7: Save and Export
1. **File → Save As** → `NEET_Dashboard.pbix`
2. To share: **File → Export to PDF** (available in free version)

**💡 Note:** Free Power BI Desktop lets you build reports locally. To publish online, you'd need Pro ($10/month) — but for a portfolio project, the .pbix file and PDF export are perfect.

### ✅ PHASE 5 CHECKPOINT
- [ ] Power BI Desktop installed and data imported
- [ ] 3 DAX measures created
- [ ] At least 4 visuals on your report page
- [ ] Report saved as .pbix file

---

## ⚫ PHASE 6: TESTING & VALIDATION (45 min)

> **Skills:** Data validation, cross-checking, edge cases, quality assurance

### Step 6.1: Cross-Check Data Consistency
Open your Google Sheet and your SQL database side by side. For each year, verify:
1. Does `candidates_appeared` match in both?
2. Does `integrity_status` match?
3. Do the totals add up?

### Step 6.2: Run the 25 Test Cases
Open `tests/test_cases.md` and go through each one:

**Data Integrity Tests:**
- [ ] T1: All 21 years present (2006-2026)?
- [ ] T2: No duplicate years?
- [ ] T3: candidates_appeared > 0 for every year?
- [ ] T4: candidates_affected <= candidates_appeared for every year?
- [ ] T5: Every row has a source citation?

**Statistical Validity Tests:**
- [ ] T6: P-values are between 0 and 1?
- [ ] T7: Sample sizes adequate (n ≥ 5 per group)?
- [ ] T8: Conclusions match significance level?
- [ ] T9: Effect sizes reported alongside p-values?
- [ ] T10: Confidence intervals calculated?

**Dashboard Accuracy Tests:**
- [ ] T11: KPI numbers match CSV data?
- [ ] T12: Chart bars align with data values?
- [ ] T13: All 21 years shown in heatmap?
- [ ] T14: Tooltips show correct numbers?
- [ ] T15: Layout works on mobile (resize browser to 375px)?

**SQL Validation Tests:**
- [ ] T16: Query 1 returns 21 rows?
- [ ] T17: Query 3 total investigations = sum of state_infrastructure?
- [ ] T18: Query 6 estimates are flagged as estimates?
- [ ] T19: All JOINs produce expected row counts?
- [ ] T20: NULL handling is correct (no missing data in results)?

**Ethical/Methodology Tests:**
- [ ] T21: No causal claims from correlational data?
- [ ] T22: All estimates clearly flagged?
- [ ] T23: Every data point has a source citation?
- [ ] T24: State names are neutral (not accusatory)?
- [ ] T25: Limitations are documented?

### Step 6.3: Fix Any Issues Found
If any test fails, go back and fix it. Document what you found and how you fixed it.

### ✅ PHASE 6 CHECKPOINT
- [ ] All 25 test cases reviewed
- [ ] Any failing tests documented and fixed
- [ ] Cross-check between Google Sheets, SQL, and Dashboard complete

---

## 🏁 FINAL DELIVERABLES CHECKLIST

After completing all 6 phases, you should have:

| # | Deliverable | File | Skill Demonstrated |
|---|-----------|------|-------------------|
| 1 | Google Sheet with 6 tabs, pivot tables, charts | Google Sheets (online) | Data cleaning, validation, pivot tables |
| 2 | SQLite Database | `data/neet_forensic.db` | Database design, SQL queries |
| 3 | 12 Forensic SQL Queries | `sql/forensic_queries.sql` | SQL analytics, window functions |
| 4 | Python Analysis (7 tests, 6 charts) | `python/analysis.py` + `output/` | Python, statistics, visualization |
| 5 | Interactive HTML Dashboard | `index.html` | Web development, data viz, Chart.js |
| 6 | Power BI Report | `NEET_Dashboard.pbix` | Power BI, DAX, business intelligence |
| 7 | Test Documentation | `tests/test_cases.md` | Quality assurance, validation |

---

## 📝 PORTFOLIO PRESENTATION TIPS

When showcasing this project:

1. **Lead with the insight, not the tool:** "I discovered that NEET exam integrity declined from 62% clean rate under CBSE to 25% under NTA" — not "I used Python"
2. **Show the data pipeline:** Sheets → SQL → Python → Dashboard → Power BI
3. **Highlight your methodology corrections:** "I initially planned to use Benford's Law but realized it's not applicable to bounded score data — this shows analytical maturity"
4. **Mention ethical considerations:** "I only mapped states with CBI-confirmed investigations, not speculative suspicion scores"
5. **Quantify impact:** "Dashboard covers 21 years, 6.8 crore+ total candidates, 10 confirmed breach events"

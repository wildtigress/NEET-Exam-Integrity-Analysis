"""
NEET Paper Leak Forensic Analysis — Python Data Pipeline

"""

import pandas as pd
import numpy as np
import sqlite3
import os
import json
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "neet_forensic.db"
OUTPUT_DIR = BASE_DIR / "python" / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams.update({
    'figure.figsize': (12, 6),
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
})

# ============================================================
# MODULE 1: DATA LOADING & CLEANING
# ============================================================
def load_and_clean_data():
    """Load all CSV files and perform data quality checks."""
    print("=" * 60)
    print("MODULE 1: DATA LOADING & CLEANING")
    print("=" * 60)

    # Load CSVs
    timeline = pd.read_csv(DATA_DIR / "exam_timeline.csv")
    breach = pd.read_csv(DATA_DIR / "breach_events.csv")
    impact = pd.read_csv(DATA_DIR / "student_impact.csv")
    states = pd.read_csv(DATA_DIR / "state_infrastructure.csv")
    benchmark = pd.read_csv(DATA_DIR / "exam_benchmarking.csv")

    datasets = {
        'exam_timeline': timeline,
        'breach_events': breach,
        'student_impact': impact,
        'state_infrastructure': states,
        'exam_benchmarking': benchmark
    }

    # Data Quality Report
    print("\n--- DATA QUALITY REPORT ---")
    for name, df in datasets.items():
        total_cells = df.shape[0] * df.shape[1]
        missing = df.isnull().sum().sum()
        completeness = round(100 * (1 - missing / total_cells), 1)
        dupes = df.duplicated().sum()
        print(f"\n  {name}:")
        print(f"    Rows: {df.shape[0]}, Columns: {df.shape[1]}")
        print(f"    Completeness: {completeness}%")
        print(f"    Duplicates: {dupes}")
        print(f"    Missing by column: {df.isnull().sum()[df.isnull().sum() > 0].to_dict() or 'None'}")

    # Type casting
    timeline['year'] = timeline['year'].astype(int)
    timeline['candidates_affected'] = timeline['candidates_affected'].fillna(0).astype(int)
    timeline['arrests_made'] = timeline['arrests_made'].fillna(0).astype(int)

    impact['year'] = impact['year'].astype(int)
    impact['student_suicides_national_exam_related'] = pd.to_numeric(
        impact['student_suicides_national_exam_related'], errors='coerce'
    )
    impact['kota_student_suicides'] = pd.to_numeric(
        impact['kota_student_suicides'], errors='coerce'
    )

    # Outlier detection (IQR method) on candidate counts
    print("\n--- OUTLIER DETECTION (IQR) ---")
    for col in ['candidates_appeared', 'candidates_affected']:
        q1, q3 = timeline[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = timeline[(timeline[col] < lower) | (timeline[col] > upper)]
        print(f"  {col}: {len(outliers)} outliers detected")
        if len(outliers) > 0:
            for _, row in outliers.iterrows():
                print(f"    Year {row['year']}: {row[col]:,}")

    return datasets


# ============================================================
# MODULE 2: SQLITE DATABASE CREATION
# ============================================================
def create_database(datasets):
    """Create SQLite database from CSV data."""
    print("\n" + "=" * 60)
    print("MODULE 2: SQLITE DATABASE CREATION")
    print("=" * 60)

    if DB_PATH.exists():
        os.remove(DB_PATH)

    conn = sqlite3.connect(str(DB_PATH))

    # Load schema
    schema_path = BASE_DIR / "sql" / "create_database.sql"
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        print(f"  Schema loaded from {schema_path}")

    # Insert data
    for name, df in datasets.items():
        df.to_sql(name, conn, if_exists='replace', index=False)
        print(f"  Loaded {len(df)} rows into '{name}'")

    # Verify
    cursor = conn.cursor()
    for table in datasets.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  Verified: {table} has {count} rows")

    conn.close()
    print(f"\n  Database saved to: {DB_PATH}")
    return str(DB_PATH)


# ============================================================
# MODULE 3: STATISTICAL TESTS (7 tests with p-values)
# ============================================================
def run_statistical_tests(datasets):
    """Run 7 statistical tests with p-values and interpretations."""
    print("\n" + "=" * 60)
    print("MODULE 3: STATISTICAL ANALYSIS (7 TESTS)")
    print("=" * 60)

    timeline = datasets['exam_timeline']
    impact = datasets['student_impact']
    states = datasets['state_infrastructure']

    results = []

    # ---- TEST 1: Chi-square goodness-of-fit ----
    # Are integrity categories evenly distributed or skewed?
    print("\n--- T1: Chi-Square Goodness-of-Fit ---")
    print("  H0: Integrity statuses are equally distributed across years")
    observed = timeline['integrity_status'].value_counts()
    n = len(timeline)
    expected = [n / 4] * 4  # Equal distribution assumption
    observed_vals = [observed.get(s, 0) for s in ['Clean', 'Minor', 'Major', 'Cancelled']]
    chi2, p_value = stats.chisquare(observed_vals, f_exp=expected)
    sig = "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0"
    print(f"  Observed: Clean={observed_vals[0]}, Minor={observed_vals[1]}, Major={observed_vals[2]}, Cancelled={observed_vals[3]}")
    print(f"  Chi² = {chi2:.4f}, p = {p_value:.6f}")
    print(f"  Result: {sig} — {'Statuses are NOT equally distributed' if p_value < 0.05 else 'Cannot conclude unequal distribution'}")
    results.append({'test': 'Chi-Square GoF', 'statistic': chi2, 'p_value': p_value, 'result': sig})

    # ---- TEST 2: Mann-Whitney U ----
    # Are candidate counts different in disrupted vs clean years?
    print("\n--- T2: Mann-Whitney U Test ---")
    print("  H0: Candidate counts are same in disrupted vs clean years")
    disrupted = timeline[timeline['integrity_status'].isin(['Major', 'Cancelled'])]['candidates_appeared']
    clean = timeline[timeline['integrity_status'] == 'Clean']['candidates_appeared']
    if len(disrupted) >= 2 and len(clean) >= 2:
        u_stat, p_value = stats.mannwhitneyu(disrupted, clean, alternative='two-sided')
        sig = "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0"
        print(f"  Disrupted years median: {disrupted.median():,.0f}")
        print(f"  Clean years median: {clean.median():,.0f}")
        print(f"  U = {u_stat:.4f}, p = {p_value:.6f}")
        print(f"  Result: {sig}")
        results.append({'test': 'Mann-Whitney U', 'statistic': u_stat, 'p_value': p_value, 'result': sig})
    else:
        print("  Insufficient data for test")

    # ---- TEST 3: Spearman Rank Correlation ----
    # Correlation between investigation involvement and PHC vacancy
    print("\n--- T3: Spearman Rank Correlation ---")
    print("  H0: No correlation between investigation involvement and PHC vacancy")
    inv_counts = states['investigation_involvement_count']
    vacancy = states['phc_doctor_vacancy_pct']
    rho, p_value = stats.spearmanr(inv_counts, vacancy)
    sig = "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0"
    print(f"  Spearman ρ = {rho:.4f}, p = {p_value:.6f}")
    print(f"  Result: {sig} — {'Significant correlation' if p_value < 0.05 else 'No significant correlation'}")
    results.append({'test': 'Spearman Correlation', 'statistic': rho, 'p_value': p_value, 'result': sig})

    # ---- TEST 4: Fisher's Exact Test ----
    # Are high-investigation states overrepresented among high-seat states?
    print("\n--- T4: Fisher's Exact Test ---")
    print("  H0: Investigation involvement is independent of medical seat count")
    median_seats = states['mbbs_seats_total'].median()
    high_seats_high_inv = len(states[(states['mbbs_seats_total'] > median_seats) & (states['investigation_involvement_count'] > 0)])
    high_seats_low_inv = len(states[(states['mbbs_seats_total'] > median_seats) & (states['investigation_involvement_count'] == 0)])
    low_seats_high_inv = len(states[(states['mbbs_seats_total'] <= median_seats) & (states['investigation_involvement_count'] > 0)])
    low_seats_low_inv = len(states[(states['mbbs_seats_total'] <= median_seats) & (states['investigation_involvement_count'] == 0)])
    contingency = [[high_seats_high_inv, high_seats_low_inv], [low_seats_high_inv, low_seats_low_inv]]
    odds, p_value = stats.fisher_exact(contingency)
    sig = "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0"
    print(f"  Contingency: {contingency}")
    print(f"  Odds Ratio = {odds:.4f}, p = {p_value:.6f}")
    print(f"  Result: {sig}")
    results.append({'test': 'Fisher Exact', 'statistic': odds, 'p_value': p_value, 'result': sig})

    # ---- TEST 5: Wilcoxon Signed-Rank ----
    # Do female candidate percentages change in disruption years?
    print("\n--- T5: Wilcoxon Signed-Rank Test ---")
    print("  H0: Female % does not differ between consecutive disrupted/clean year pairs")
    merged = timeline.merge(impact[['year', 'female_candidate_pct']], on='year', how='inner')
    merged = merged.dropna(subset=['female_candidate_pct'])
    if len(merged) >= 6:
        # Compare year-over-year changes
        merged['female_change'] = merged['female_candidate_pct'].diff()
        merged['is_disrupted'] = merged['integrity_status'].isin(['Major', 'Cancelled'])
        disrupted_changes = merged[merged['is_disrupted']]['female_change'].dropna()
        if len(disrupted_changes) >= 2:
            w_stat, p_value = stats.wilcoxon(disrupted_changes)
            sig = "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0"
            print(f"  W = {w_stat:.4f}, p = {p_value:.6f}")
            print(f"  Result: {sig}")
            results.append({'test': 'Wilcoxon Signed-Rank', 'statistic': w_stat, 'p_value': p_value, 'result': sig})
        else:
            print("  Insufficient disrupted year pairs for test")
    else:
        print("  Insufficient data for test")

    # ---- TEST 6: Linear Regression ----
    # Is breach severity increasing over time?
    print("\n--- T6: Linear Regression (Severity Trend) ---")
    print("  H0: No linear trend in breach severity over time")
    severity_map = {'Clean': 0, 'Minor': 1, 'Major': 3, 'Cancelled': 5}
    timeline['severity_score'] = timeline['integrity_status'].map(severity_map)
    slope, intercept, r_value, p_value, std_err = stats.linregress(timeline['year'], timeline['severity_score'])
    sig = "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0"
    print(f"  Slope = {slope:.4f}, R² = {r_value**2:.4f}, p = {p_value:.6f}")
    print(f"  Interpretation: Severity {'IS increasing' if slope > 0 and p_value < 0.05 else 'shows no significant trend'} over time")
    print(f"  Result: {sig}")
    results.append({'test': 'Linear Regression', 'statistic': slope, 'p_value': p_value, 'result': sig})

    # ---- TEST 7: Two-Proportion Z-Test ----
    # Is CBSE era cleaner than NTA era?
    print("\n--- T7: Two-Proportion Z-Test (CBSE vs NTA) ---")
    print("  H0: Clean exam proportion is same for CBSE and NTA eras")
    cbse = timeline[timeline['conducting_body'] == 'CBSE']
    nta = timeline[timeline['conducting_body'] == 'NTA']
    cbse_clean = len(cbse[cbse['integrity_status'] == 'Clean'])
    nta_clean = len(nta[nta['integrity_status'] == 'Clean'])
    n_cbse, n_nta = len(cbse), len(nta)
    p1, p2 = cbse_clean / n_cbse, nta_clean / n_nta
    p_pool = (cbse_clean + nta_clean) / (n_cbse + n_nta)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n_cbse + 1/n_nta))
    if se > 0:
        z_stat = (p1 - p2) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        z_stat, p_value = 0, 1.0
    sig = "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0"
    print(f"  CBSE clean rate: {cbse_clean}/{n_cbse} = {p1:.1%}")
    print(f"  NTA clean rate: {nta_clean}/{n_nta} = {p2:.1%}")
    print(f"  Z = {z_stat:.4f}, p = {p_value:.6f}")
    print(f"  Result: {sig}")
    results.append({'test': 'Two-Proportion Z', 'statistic': z_stat, 'p_value': p_value, 'result': sig})

    # Summary table
    print("\n" + "=" * 60)
    print("STATISTICAL TEST SUMMARY")
    print("=" * 60)
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))

    # Save results
    results_df.to_csv(OUTPUT_DIR / "statistical_test_results.csv", index=False)
    print(f"\n  Results saved to: {OUTPUT_DIR / 'statistical_test_results.csv'}")

    return results_df


# ============================================================
# MODULE 4: VISUALIZATIONS
# ============================================================
def generate_visualizations(datasets):
    """Generate publication-quality charts."""
    print("\n" + "=" * 60)
    print("MODULE 4: VISUALIZATION GENERATION")
    print("=" * 60)

    timeline = datasets['exam_timeline']
    impact = datasets['student_impact']
    states = datasets['state_infrastructure']

    # Chart 1: Integrity Timeline
    fig, ax = plt.subplots(figsize=(14, 5))
    colors = {'Clean': '#639922', 'Minor': '#BA7517', 'Major': '#E24B4A', 'Cancelled': '#A32D2D'}
    bar_colors = [colors[s] for s in timeline['integrity_status']]
    severity_map = {'Clean': 4, 'Minor': 3, 'Major': 1, 'Cancelled': 0}
    heights = [severity_map[s] for s in timeline['integrity_status']]
    ax.bar(timeline['year'].astype(str), heights, color=bar_colors, edgecolor='white', linewidth=0.5)
    ax.set_title('NEET/AIPMT Exam Integrity Score (2006–2026)', fontweight='bold')
    ax.set_ylabel('Integrity Score (4=Clean, 0=Cancelled)')
    ax.set_xlabel('Year')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "01_integrity_timeline.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: 01_integrity_timeline.png")

    # Chart 2: Candidates Appeared vs Affected
    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(timeline))
    w = 0.35
    ax.bar(x - w/2, timeline['candidates_appeared'] / 100000, w, label='Appeared (Lakhs)', color='#85B7EB')
    ax.bar(x + w/2, timeline['candidates_affected'] / 100000, w, label='Affected (Lakhs)', color='#E24B4A')
    ax.set_xticks(x)
    ax.set_xticklabels(timeline['year'].astype(str), rotation=45, ha='right')
    ax.set_title('NEET Candidates: Appeared vs Directly Affected', fontweight='bold')
    ax.set_ylabel('Candidates (Lakhs)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "02_appeared_vs_affected.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: 02_appeared_vs_affected.png")

    # Chart 3: Student Suicides Trend
    suicide_data = impact.dropna(subset=['student_suicides_national_exam_related'])
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(suicide_data['year'], suicide_data['student_suicides_national_exam_related'],
             'o-', color='#E24B4A', linewidth=2, markersize=6, label='National exam-related suicides')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('National Exam-Related Suicides', color='#E24B4A')
    ax1.tick_params(axis='y', labelcolor='#E24B4A')

    kota_data = impact.dropna(subset=['kota_student_suicides'])
    ax2 = ax1.twinx()
    ax2.bar(kota_data['year'], kota_data['kota_student_suicides'],
            alpha=0.4, color='#BA7517', label='Kota suicides')
    ax2.set_ylabel('Kota Student Suicides', color='#BA7517')
    ax2.tick_params(axis='y', labelcolor='#BA7517')

    ax1.set_title('Student Suicides: National Trend + Kota Overlay', fontweight='bold')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "03_suicide_trend.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: 03_suicide_trend.png")

    # Chart 4: State Investigation Heatmap
    inv_states = states[states['investigation_involvement_count'] > 0].sort_values(
        'investigation_involvement_count', ascending=True
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    colors_bar = ['#BA7517' if x < 3 else '#E24B4A' if x < 4 else '#A32D2D'
                  for x in inv_states['investigation_involvement_count']]
    ax.barh(inv_states['state'], inv_states['investigation_involvement_count'], color=colors_bar)
    ax.set_xlabel('Number of CBI/Police Investigations Involved')
    ax.set_title('States by Confirmed Investigation Involvement', fontweight='bold')
    for i, v in enumerate(inv_states['investigation_involvement_count']):
        ax.text(v + 0.1, i, str(v), va='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "04_state_investigations.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: 04_state_investigations.png")

    # Chart 5: Correlation Heatmap
    numeric_cols = timeline[['year', 'candidates_registered', 'candidates_appeared',
                             'candidates_qualified', 'candidates_affected', 'arrests_made']].copy()
    numeric_cols['severity_score'] = timeline['integrity_status'].map(
        {'Clean': 0, 'Minor': 1, 'Major': 3, 'Cancelled': 5}
    )
    fig, ax = plt.subplots(figsize=(8, 6))
    corr = numeric_cols.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlGn_r',
                center=0, ax=ax, square=True)
    ax.set_title('Correlation Matrix: NEET Exam Variables', fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "05_correlation_heatmap.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: 05_correlation_heatmap.png")

    # Chart 6: CBSE vs NTA Era Box Plot
    timeline_copy = timeline.copy()
    timeline_copy['era'] = timeline_copy['conducting_body']
    severity_map = {'Clean': 0, 'Minor': 1, 'Major': 3, 'Cancelled': 5}
    timeline_copy['severity'] = timeline_copy['integrity_status'].map(severity_map)
    fig, ax = plt.subplots(figsize=(8, 5))
    cbse_data = timeline_copy[timeline_copy['era'] == 'CBSE']['severity']
    nta_data = timeline_copy[timeline_copy['era'] == 'NTA']['severity']
    bp = ax.boxplot([cbse_data, nta_data], labels=['CBSE Era\n(2006–2018)', 'NTA Era\n(2019–2026)'],
                    patch_artist=True)
    bp['boxes'][0].set_facecolor('#85B7EB')
    bp['boxes'][1].set_facecolor('#E24B4A')
    ax.set_ylabel('Severity Score (0=Clean, 5=Cancelled)')
    ax.set_title('Exam Disruption Severity: CBSE vs NTA Era', fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "06_cbse_vs_nta.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: 06_cbse_vs_nta.png")

    print(f"\n  All charts saved to: {OUTPUT_DIR}")


# ============================================================
# MODULE 5: API INTEGRATION DEMO
# ============================================================
def api_integration_demo():
    """Demonstrate API concepts for data collection."""
    print("\n" + "=" * 60)
    print("MODULE 5: API INTEGRATION DEMO")
    print("=" * 60)

    # Demo 1: Structuring data as JSON API response
    api_response = {
        "endpoint": "/api/v1/neet/integrity",
        "description": "NEET Exam Integrity Status API",
        "data_source": "Compiled from NTA, CBI, Supreme Court records",
        "last_updated": "2026-05-22",
        "total_records": 21,
        "sample_record": {
            "year": 2024,
            "exam_name": "NEET-UG",
            "integrity_status": "Major",
            "candidates_appeared": 2400000,
            "candidates_affected": 2400000,
            "breach_type": "Paper Theft + Grace Mark Fraud",
            "source": "CBI FIR 2024; Supreme Court order Aug 2024"
        }
    }
    print(f"\n  Sample API Response Structure:")
    print(f"  {json.dumps(api_response, indent=2)[:500]}...")

    # Demo 2: Fetching data from public endpoint (NTA website structure)
    print("\n  API Data Sources (public endpoints):")
    endpoints = [
        {"name": "NTA NEET Results", "url": "https://exams.nta.ac.in/NEET/", "type": "Web scraping required", "status": "Active"},
        {"name": "NCRB Data", "url": "https://ncrb.gov.in/accidental-deaths-suicides-in-india", "type": "PDF download", "status": "Active"},
        {"name": "NMC College List", "url": "https://www.nmc.org.in/information-desk/college-and-course-search", "type": "Search API", "status": "Active"},
    ]
    for ep in endpoints:
        print(f"    {ep['name']}: {ep['url']} ({ep['type']})")

    # Demo 3: SQLite as local API backend
    print("\n  Local Database API Layer:")
    print("  SQLite serves as the local data store that could back a REST API")
    print("  Example: Flask/FastAPI endpoint querying neet_forensic.db")

    # Save API structure
    with open(OUTPUT_DIR / "api_structure.json", 'w') as f:
        json.dump(api_response, f, indent=2)
    print(f"\n  API structure saved to: {OUTPUT_DIR / 'api_structure.json'}")


# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("  NEET PAPER LEAK FORENSIC ANALYSIS")
    print("  Real Data from Verified Public Sources")
    print("=" * 60)

    # Phase 1: Load and clean
    datasets = load_and_clean_data()

    # Phase 2: Create database
    db_path = create_database(datasets)

    # Phase 3: Statistical tests
    test_results = run_statistical_tests(datasets)

    # Phase 4: Visualizations
    generate_visualizations(datasets)

    # Phase 5: API demo
    api_integration_demo()

    print("\n" + "=" * 60)
    print("  ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"  Database: {db_path}")
    print(f"  Charts: {OUTPUT_DIR}")
    print(f"  Test Results: {OUTPUT_DIR / 'statistical_test_results.csv'}")
    print(f"  API Structure: {OUTPUT_DIR / 'api_structure.json'}")


if __name__ == "__main__":
    main()

import pandas as pd
import numpy as np
import sqlite3
import json
import os
import sys
from pathlib import Path

# Add parent to path so we can import analysis module
sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SQL_DIR = BASE_DIR / "sql"
DB_PATH = DATA_DIR / "neet_forensic.db"
OUTPUT_DIR = BASE_DIR / "python" / "output"
SQL_OUTPUT_DIR = OUTPUT_DIR / "sql_query_results"

def step1_create_database():
    """Create SQLite database from CSVs + SQL schema."""
    print("\n" + "=" * 60)
    print("  STEP 1: CREATING SQLITE DATABASE FROM CSVs")
    print("=" * 60)

    # Remove old DB if exists
    if DB_PATH.exists():
        os.remove(DB_PATH)
        print(f"  Removed old database: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))

    # Run schema SQL
    schema_path = SQL_DIR / "create_database.sql"
    if schema_path.exists():
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        print(f"  Schema loaded from: {schema_path.name}")
    else:
        print(f"  Schema file not found: {schema_path}")
        return None

    # Load each CSV into the database
    csv_files = {
        'exam_timeline': 'exam_timeline.csv',
        'breach_events': 'breach_events.csv',
        'student_impact': 'student_impact.csv',
        'state_infrastructure': 'state_infrastructure.csv',
        'exam_benchmarking': 'exam_benchmarking.csv'
    }

    for table_name, csv_file in csv_files.items():
        csv_path = DATA_DIR / csv_file
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"  Loaded {len(df)} rows → '{table_name}'")
        else:
            print(f"  CSV not found: {csv_file}")

    # Re-create views (they were dropped when we replaced tables)
    views_sql = """
    DROP VIEW IF EXISTS v_era_comparison;
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

    DROP VIEW IF EXISTS v_state_risk_ranking;
    CREATE VIEW v_state_risk_ranking AS
    SELECT
        state, state_code, investigation_involvement_count, investigation_years,
        medical_colleges_total, mbbs_seats_total, phc_doctor_vacancy_pct,
        CASE
            WHEN investigation_involvement_count >= 4 THEN 'Critical'
            WHEN investigation_involvement_count >= 2 THEN 'High'
            WHEN investigation_involvement_count = 1 THEN 'Moderate'
            ELSE 'Low'
        END AS risk_level
    FROM state_infrastructure
    ORDER BY investigation_involvement_count DESC;
    """
    conn.executescript(views_sql)
    print("  Views created: v_era_comparison, v_state_risk_ranking")

    # Verify
    cursor = conn.cursor()
    print("\n  --- Verification ---")
    for table in csv_files.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows ✓")

    conn.close()
    print(f"\n  Database saved: {DB_PATH}")
    return str(DB_PATH)


def step2_run_forensic_queries():
    """Run all 12 forensic SQL queries and save results as CSVs."""
    print("\n" + "=" * 60)
    print("  STEP 2: RUNNING 12 FORENSIC SQL QUERIES")
    print("=" * 60)

    SQL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    # Read the forensic queries file
    queries_path = SQL_DIR / "forensic_queries.sql"
    if not queries_path.exists():
        print(f"  Queries file not found: {queries_path}")
        return

    with open(queries_path, 'r', encoding='utf-8') as f:
        full_sql = f.read()

    # Split into individual queries (split on the separator comments)
    import re
    query_blocks = re.split(r'-- ={50,}', full_sql)

    query_num = 0
    for block in query_blocks:
        # Extract SELECT statements
        selects = re.findall(r'(SELECT[\s\S]*?;)', block, re.IGNORECASE)
        for sql in selects:
            query_num += 1
            # Extract query title from comments
            title_match = re.search(r'-- QUERY \d+:\s*(.+)', block)
            title = title_match.group(1).strip() if title_match else f"Query {query_num}"

            try:
                df = pd.read_sql_query(sql, conn)
                filename = f"query_{query_num:02d}_{title[:40].replace(' ', '_').replace('—','').replace('/','_').lower()}.csv"
                df.to_csv(SQL_OUTPUT_DIR / filename, index=False)
                print(f"  Q{query_num}: {title} → {len(df)} rows")
            except Exception as e:
                print(f"  Q{query_num}: {title} — {str(e)[:80]}")

    conn.close()
    print(f"\n  Query results saved: {SQL_OUTPUT_DIR}")


def step3_export_dashboard_json():
    """Export integrated data as JSON for the dashboard."""
    print("\n" + "=" * 60)
    print("  STEP 3: EXPORTING DASHBOARD DATA (JSON)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    dashboard_data = {}

    # Timeline data
    timeline = pd.read_sql_query("SELECT * FROM exam_timeline ORDER BY year", conn)
    dashboard_data['timeline'] = timeline.to_dict(orient='records')

    # Era comparison from view
    try:
        era = pd.read_sql_query("SELECT * FROM v_era_comparison", conn)
        dashboard_data['era_comparison'] = era.to_dict(orient='records')
    except:
        pass

    # State risk from view
    try:
        risk = pd.read_sql_query("SELECT * FROM v_state_risk_ranking WHERE investigation_involvement_count > 0", conn)
        dashboard_data['state_risk'] = risk.to_dict(orient='records')
    except:
        pass

    # Breach events
    breach = pd.read_sql_query("SELECT * FROM breach_events ORDER BY year", conn)
    dashboard_data['breach_events'] = breach.to_dict(orient='records')

    # Student impact
    impact = pd.read_sql_query("SELECT * FROM student_impact ORDER BY year", conn)
    dashboard_data['student_impact'] = impact.to_dict(orient='records')

    # Benchmarking
    bench = pd.read_sql_query("SELECT * FROM exam_benchmarking", conn)
    dashboard_data['benchmarking'] = bench.to_dict(orient='records')

    # Key statistics
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM exam_timeline WHERE integrity_status='Clean'")
    clean_count = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(candidates_affected) FROM exam_timeline")
    total_affected = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(arrests_made) FROM exam_timeline")
    total_arrests = cursor.fetchone()[0]

    dashboard_data['kpi'] = {
        'clean_exams': clean_count,
        'total_years': len(timeline),
        'total_affected': int(total_affected or 0),
        'total_arrests': int(total_arrests or 0),
        'breach_events': len(breach)
    }

    conn.close()

    json_path = OUTPUT_DIR / "dashboard_data.json"
    with open(json_path, 'w') as f:
        json.dump(dashboard_data, f, indent=2, default=str)

    print(f"  Dashboard JSON exported: {json_path}")
    print(f"  KPIs: {clean_count} clean exams, {total_affected:,} affected, {total_arrests} arrests")


def step4_run_analysis():
    """Run the full statistical analysis from analysis.py."""
    print("\n" + "=" * 60)
    print("  STEP 4: RUNNING STATISTICAL ANALYSIS & CHARTS")
    print("=" * 60)

    try:
        from analysis import load_and_clean_data, run_statistical_tests, generate_visualizations, api_integration_demo
        datasets = load_and_clean_data()
        run_statistical_tests(datasets)
        generate_visualizations(datasets)
        api_integration_demo()
        print("\n  Full analysis complete!")
    except ImportError as e:
        print(f"\n  Could not import analysis module: {e}")
        print("  Make sure you have all dependencies: pip install pandas numpy scipy matplotlib seaborn")
    except Exception as e:
        print(f"\n  Analysis error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "=" * 60)
    print("  🔬 NEET FORENSIC DASHBOARD — AUTOMATED PIPELINE")
    print("  Sheets → Python → SQLite → Charts → Dashboard")
    print("=" * 60)

    # Step 1: Create database
    db = step1_create_database()
    if not db:
        print("\n❌ Database creation failed. Fix errors above and retry.")
        return

    # Step 2: Run forensic queries
    step2_run_forensic_queries()

    # Step 3: Export dashboard JSON
    step3_export_dashboard_json()

    # Step 4: Run statistical analysis + charts
    step4_run_analysis()

    # Final summary
    print("\n" + "=" * 60)
    print("  ALL DONE! Here's what was created:")
    print("=" * 60)
    print(f"  SQLite Database:    {DB_PATH}")
    print(f"  SQL Query Results:  {SQL_OUTPUT_DIR}")
    print(f"  Charts (PNG):       {OUTPUT_DIR}")
    print(f"  Dashboard JSON:     {OUTPUT_DIR / 'dashboard_data.json'}")
    print(f"  Stats Results:      {OUTPUT_DIR / 'statistical_test_results.csv'}")
    print()
    print("  NEXT STEPS:")
    print("  1. Open DB Browser → File → Open Database → data/neet_forensic.db")
    print("     → Explore tables, run your own queries!")
    print("  2. Open index.html in your browser → see the interactive dashboard")
    print("  3. Check python/output/ → see all charts and query results")


if __name__ == "__main__":
    main()

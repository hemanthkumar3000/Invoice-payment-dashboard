"""
run_all.py
----------
Master pipeline execution script.
Executes the entire Invoice-Payment Reconciliation project in one command:
  1. Generates synthetic raw invoices and payments with real-world anomalies.
  2. Runs Pandas data cleaning and reconciliation pipeline.
  3. Builds SQLite database and executes analytical SQL queries.
  4. Generates executive Excel workbook with pivot sheets and conditional formatting.
  5. Builds interactive HTML dashboard companion.
  6. Runs data integrity and mathematical invariant verification suite.
"""

import sys
import subprocess
import time

def run_step(step_num, title, command):
    print("\n" + "=" * 70)
    print(f">> STEP {step_num}: {title.upper()}")
    print("=" * 70)
    start_t = time.time()
    res = subprocess.run([sys.executable] + command, capture_output=False)
    elapsed = time.time() - start_t
    if res.returncode != 0:
        print(f"[ERROR] Step {step_num} failed with return code {res.returncode}")
        sys.exit(res.returncode)
    print(f">> Completed in {elapsed:.2f} seconds.")

def main():
    print("""
    ========================================================================
     INVOICE–PAYMENT RECONCILIATION & REVENUE DASHBOARD PIPELINE
     Cross-Source Financial Intelligence & Data Engineering
    ========================================================================
    """)
    t0 = time.time()

    # Step 1: Generate synthetic raw data
    run_step(1, "Generate Synthetic Data (Invoices & Payments)", ["src/generate_synthetic_data.py"])

    # Step 2: Data Cleaning & Reconciliation with Pandas
    run_step(2, "Clean & Reconcile Data (Pandas Pipeline)", ["src/reconcile_data.py"])

    # Step 3: SQL Database & Analytical Queries
    run_step(3, "Load SQLite Database & Execute Analytical SQL", ["src/run_sql_analysis.py"])

    # Step 4: Executive Excel Workbook
    run_step(4, "Build Excel Workbook with Pivots & Conditional Formatting", ["src/create_excel_report.py"])

    # Step 5: Interactive HTML Dashboard Companion
    run_step(5, "Build Interactive Web Dashboard (Power BI Companion)", ["src/build_interactive_dashboard.py"])

    # Step 6: Verification & Test Suite
    run_step(6, "Run Data Integrity & Invariant Tests (pytest)", ["-m", "pytest", "tests/test_reconciliation.py"])

    total_time = time.time() - t0
    print("\n" + "=" * 70)
    print(f">> [SUCCESS] PIPELINE COMPLETED SUCCESSFULLY IN {total_time:.2f}s!")
    print("=" * 70)
    print("Generated Artifacts:")
    print("  * Raw Datasets      : data/raw/invoices.csv, data/raw/payments.csv")
    print("  * Reconciled Master : data/processed/reconciled_invoices.csv, reconciled_invoices.csv")
    print("  * Clean Payments    : data/processed/cleaned_payments.csv")
    print("  * SQLite Database   : finance_reconciliation.db")
    print("  * SQL Query Reports : reports/sql_analysis_results.md")
    print("  * Excel Report      : reports/reconciliation_report.xlsx, reconciliation_report.xlsx")
    print("  * Power BI Assets   : power_bi/DAX_Measures.dax, power_bi/PowerQuery_M_Script.m, power_bi/PowerBI_Setup_Guide.md")
    print("  * Web Dashboard     : reports/interactive_dashboard.html, interactive_dashboard.html")
    print("========================================================================\n")

if __name__ == "__main__":
    main()

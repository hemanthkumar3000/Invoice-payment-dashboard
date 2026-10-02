"""
run_sql_analysis.py
-------------------
Executes SQL analysis against a local SQLite database (finance_reconciliation.db).
Loads raw and reconciled tables, runs analytical queries, formats results,
and outputs a markdown audit report.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = "finance_reconciliation.db"
SCHEMA_PATH = "sql/schema.sql"
RECON_CSV = "data/processed/reconciled_invoices.csv"
CLEAN_PAY_CSV = "data/processed/cleaned_payments.csv"
RAW_INV_CSV = "data/raw/invoices.csv"
REPORT_MD = "reports/sql_analysis_results.md"

def build_database():
    print(f">> Initializing SQLite Database at '{DB_PATH}'...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # Ingest clean datasets into SQLite
    df_raw_inv = pd.read_csv(RAW_INV_CSV).drop_duplicates(subset=["Invoice_ID"])
    df_clean_pay = pd.read_csv(CLEAN_PAY_CSV)
    df_recon = pd.read_csv(RECON_CSV)

    df_raw_inv.to_sql("raw_invoices", conn, if_exists="replace", index=False)
    df_clean_pay.to_sql("raw_payments", conn, if_exists="replace", index=False)
    df_recon.to_sql("reconciled_invoices", conn, if_exists="replace", index=False)

    conn.commit()
    print(">> Tables successfully populated.")
    return conn

def execute_queries(conn):
    print(">> Running Analytical SQL Queries...")
    
    queries = {
        "1. Department Revenue, Collections & Outstanding Balances": """
            SELECT
                Department,
                COUNT(*) AS Total_Invoices,
                PRINTF('$%,.2f', SUM(Invoice_Amount)) AS Invoiced_Amount,
                PRINTF('$%,.2f', SUM(Total_Paid)) AS Collected_Amount,
                PRINTF('$%,.2f', SUM(Outstanding_Amount)) AS Outstanding_Amount,
                ROUND((SUM(Total_Paid) / SUM(Invoice_Amount)) * 100, 2) || '%' AS Collection_Rate
            FROM reconciled_invoices
            GROUP BY Department
            ORDER BY SUM(Outstanding_Amount) DESC;
        """,
        
        "2. Top 10 Customers with Largest Outstanding Balances": """
            SELECT
                Customer,
                COUNT(*) AS Invoices,
                PRINTF('$%,.2f', SUM(Invoice_Amount)) AS Invoiced,
                PRINTF('$%,.2f', SUM(Total_Paid)) AS Collected,
                PRINTF('$%,.2f', SUM(Outstanding_Amount)) AS Total_Outstanding,
                ROUND((SUM(Total_Paid) / SUM(Invoice_Amount)) * 100, 2) || '%' AS Collection_Rate,
                MAX(Days_Overdue) AS Max_Days_Overdue
            FROM reconciled_invoices
            WHERE Outstanding_Amount > 0
            GROUP BY Customer
            ORDER BY SUM(Outstanding_Amount) DESC
            LIMIT 10;
        """,
        
        "3. Payment Status & Cash Fulfillment Distribution": """
            SELECT
                Payment_Status,
                COUNT(*) AS Invoice_Count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reconciled_invoices), 1) || '%' AS Pct_Volume,
                PRINTF('$%,.2f', SUM(Invoice_Amount)) AS Invoiced_Value,
                PRINTF('$%,.2f', SUM(Total_Paid)) AS Collected_Value,
                PRINTF('$%,.2f', SUM(Outstanding_Amount)) AS Outstanding_Value,
                ROUND(AVG(Days_Overdue), 1) AS Avg_Days_Overdue
            FROM reconciled_invoices
            GROUP BY Payment_Status
            ORDER BY SUM(Invoice_Amount) DESC;
        """,
        
        "4. Accounts Receivable Aging Breakdown (Delinquency Risk)": """
            SELECT
                Aging_Bucket,
                COUNT(*) AS Overdue_Count,
                PRINTF('$%,.2f', SUM(Outstanding_Amount)) AS Outstanding_Balance,
                ROUND(SUM(Outstanding_Amount) * 100.0 / (SELECT SUM(Outstanding_Amount) FROM reconciled_invoices), 1) || '%' AS Pct_Of_Total_AR,
                ROUND(AVG(Days_Overdue), 1) AS Avg_Days_Overdue
            FROM reconciled_invoices
            WHERE Outstanding_Amount > 0
            GROUP BY Aging_Bucket
            ORDER BY 
                CASE Aging_Bucket
                    WHEN '1-30 Days' THEN 1
                    WHEN '31-60 Days' THEN 2
                    WHEN '61-90 Days' THEN 3
                    WHEN '90+ Days' THEN 4
                    ELSE 5
                END;
        """,
        
        "5. Monthly Invoiced vs Collected Cash Velocity": """
            SELECT
                SUBSTR(Invoice_Date, 1, 7) AS Month,
                COUNT(*) AS Invoices,
                PRINTF('$%,.2f', SUM(Invoice_Amount)) AS Invoiced,
                PRINTF('$%,.2f', SUM(Total_Paid)) AS Collected,
                PRINTF('$%,.2f', SUM(Outstanding_Amount)) AS Outstanding,
                ROUND((SUM(Total_Paid) / SUM(Invoice_Amount)) * 100, 1) || '%' AS Velocity_Rate
            FROM reconciled_invoices
            GROUP BY SUBSTR(Invoice_Date, 1, 7)
            ORDER BY Month ASC;
        """,
        
        "6. Operational Late Payment Analysis by Department": """
            SELECT
                Department,
                COUNT(*) AS Total_Invoices,
                SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1 ELSE 0 END) AS Late_Invoices,
                ROUND(SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) || '%' AS Late_Rate_Pct,
                ROUND(AVG(CASE WHEN Days_Overdue > 0 THEN Days_Overdue ELSE NULL END), 1) AS Avg_Days_Late
            FROM reconciled_invoices
            GROUP BY Department
            ORDER BY SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*) DESC;
        """,

        "7. Ledger Integrity Verification (Payments vs Invoices)": """
            SELECT
                'Raw Payments Subledger' AS Source,
                COUNT(DISTINCT Invoice_ID) AS Invoices_With_Payments,
                PRINTF('$%,.2f', SUM(Payment_Amount)) AS Total_Cash_Accounted
            FROM raw_payments
            UNION ALL
            SELECT
                'Reconciled General Ledger' AS Source,
                COUNT(DISTINCT Invoice_ID) AS Invoices_With_Payments,
                PRINTF('$%,.2f', SUM(Total_Paid)) AS Total_Cash_Accounted
            FROM reconciled_invoices
            WHERE Total_Paid > 0;
        """
    }

    report_lines = [
        "# SQL Financial Analysis & Reconciliation Report",
        f"**Generated On:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Database:** SQLite (`finance_reconciliation.db`)",
        "",
        "---",
        ""
    ]

    for title, query in queries.items():
        print(f"\n>> {title}:")
        df_res = pd.read_sql_query(query, conn)
        print(df_res.to_string(index=False))
        
        report_lines.append(f"### {title}")
        report_lines.append("```sql" + query + "```")
        report_lines.append(df_res.to_markdown(index=False))
        report_lines.append("")

    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\n>> SQL results successfully exported to: {REPORT_MD}")

if __name__ == "__main__":
    conn = build_database()
    execute_queries(conn)
    conn.close()

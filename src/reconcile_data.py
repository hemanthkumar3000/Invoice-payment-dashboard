"""
reconcile_data.py
-----------------
Automated data cleaning and financial reconciliation pipeline.

Performs:
  1. Data ingestion of raw invoices and payments.
  2. Data hygiene & anomaly resolution:
     - Deduplication of invoice and payment records.
     - String normalization (stripping leading/trailing whitespace).
     - Flexible multi-format date parsing (YYYY-MM-DD, MM/DD/YYYY).
     - Missing value handling for payment amounts and methods.
  3. Payment aggregation by Invoice_ID (Total_Paid, Payment_Count, Latest_Payment_Date).
  4. Left join reconciliation between invoices and aggregated payments.
  5. Financial metric derivations:
     - Outstanding_Amount (Invoice_Amount - Total_Paid, clamped to >= 0)
     - Payment_Status ('Paid', 'Partially Paid', 'Unpaid')
     - Days_Overdue (relative to snapshot as-of date 2026-10-01)
     - Late_Payment_Flag ('Yes', 'No')
     - Aging_Bucket ('Not Due / Settled', '1-30 Days', '31-60 Days', '61-90 Days', '90+ Days')
     - Collection_Rate_Pct ((Total_Paid / Invoice_Amount) * 100)
  6. Exporting reconciled master files to:
     - data/processed/reconciled_invoices.csv
     - data/processed/cleaned_payments.csv
     - reconciled_invoices.csv (root)
"""

import os
import json
import datetime
import pandas as pd
import numpy as np

# Reference audit snapshot date
AS_OF_DATE = pd.to_datetime("2026-10-01")

def clean_and_reconcile(raw_invoice_path="data/raw/invoices.csv",
                        raw_payment_path="data/raw/payments.csv",
                        output_dir="data/processed"):
    print("=" * 60)
    print(">> STARTING INVOICE-PAYMENT RECONCILIATION PIPELINE")
    print("=" * 60)

    # 1. Ingest Raw Datasets
    print(f">> Ingesting raw data: {raw_invoice_path}, {raw_payment_path}")
    df_inv_raw = pd.read_csv(raw_invoice_path)
    df_pay_raw = pd.read_csv(raw_payment_path)

    audit_log = {
        "raw_invoice_count": len(df_inv_raw),
        "raw_payment_count": len(df_pay_raw),
        "timestamp": datetime.datetime.now().isoformat(),
        "as_of_date": AS_OF_DATE.strftime("%Y-%m-%d"),
        "actions": []
    }

    # 2. Data Cleaning: Invoices
    print("\n[Step 1] Cleaning Invoices...")
    # Deduplication
    inv_dupes = df_inv_raw.duplicated(subset=["Invoice_ID"]).sum()
    df_inv = df_inv_raw.drop_duplicates(subset=["Invoice_ID"], keep="first").copy()
    audit_log["actions"].append(f"Removed {inv_dupes} duplicate invoice records.")
    print(f"  - Removed {inv_dupes} duplicate invoices. Clean count: {len(df_inv)}")

    # Trim whitespace
    df_inv["Customer"] = df_inv["Customer"].astype(str).str.strip()
    df_inv["Department"] = df_inv["Department"].astype(str).str.strip()
    df_inv["Invoice_ID"] = df_inv["Invoice_ID"].astype(str).str.strip()

    # Parse and standardize dates
    df_inv["Invoice_Date"] = pd.to_datetime(df_inv["Invoice_Date"], format="mixed")
    df_inv["Due_Date"] = pd.to_datetime(df_inv["Due_Date"], format="mixed")
    df_inv["Invoice_Amount"] = pd.to_numeric(df_inv["Invoice_Amount"], errors="coerce").fillna(0.0)

    # 3. Data Cleaning: Payments
    print("\n[Step 2] Cleaning Payments...")
    # Deduplication
    pay_dupes = df_pay_raw.duplicated(subset=["Payment_ID"]).sum()
    df_pay = df_pay_raw.drop_duplicates(subset=["Payment_ID"], keep="first").copy()
    audit_log["actions"].append(f"Removed {pay_dupes} duplicate payment records.")
    print(f"  - Removed {pay_dupes} duplicate payments. Clean count: {len(df_pay)}")

    # Trim whitespace
    df_pay["Payment_ID"] = df_pay["Payment_ID"].astype(str).str.strip()
    df_pay["Invoice_ID"] = df_pay["Invoice_ID"].astype(str).str.strip()
    df_pay["Payment_Method"] = df_pay["Payment_Method"].fillna("Unknown").astype(str).str.strip()

    # Handle missing / invalid payment amounts
    missing_amt_count = df_pay["Payment_Amount"].isna().sum()
    if missing_amt_count > 0:
        print(f"  - Imputing/Handling {missing_amt_count} missing Payment_Amount records (set to 0.0).")
        audit_log["actions"].append(f"Handled {missing_amt_count} records with missing Payment_Amount (filled with 0.0).")
        df_pay["Payment_Amount"] = pd.to_numeric(df_pay["Payment_Amount"], errors="coerce").fillna(0.0)

    # Standardize dates
    df_pay["Payment_Date"] = pd.to_datetime(df_pay["Payment_Date"], format="mixed")

    # 4. Aggregate Payments by Invoice_ID
    print("\n[Step 3] Aggregating Payments by Invoice_ID...")
    payment_summary = (
        df_pay.groupby("Invoice_ID", as_index=False)
        .agg(
            Total_Paid=("Payment_Amount", "sum"),
            Payment_Count=("Payment_ID", "count"),
            Latest_Payment_Date=("Payment_Date", "max"),
            Payment_Methods=("Payment_Method", lambda s: ", ".join(sorted(set(s.dropna()))))
        )
    )
    print(f"  - Grouped payments into {len(payment_summary)} unique invoice summaries.")

    # 5. Reconcile Invoices with Payment Summaries (Left Join)
    print("\n[Step 4] Merging Invoices with Payment Summaries...")
    reconciliation = df_inv.merge(
        payment_summary,
        on="Invoice_ID",
        how="left"
    )

    # Impute invoices with no payments
    reconciliation["Total_Paid"] = reconciliation["Total_Paid"].fillna(0.0)
    reconciliation["Payment_Count"] = reconciliation["Payment_Count"].fillna(0).astype(int)
    reconciliation["Payment_Methods"] = reconciliation["Payment_Methods"].fillna("None")

    # 6. Derived Financial Metrics & Status Logic
    print("\n[Step 5] Deriving Reconciled Financial Metrics...")
    # Outstanding Amount
    reconciliation["Outstanding_Amount"] = reconciliation["Invoice_Amount"] - reconciliation["Total_Paid"]
    reconciliation["Outstanding_Amount"] = reconciliation["Outstanding_Amount"].apply(lambda x: max(0.0, float(x)))

    # Collection Rate %
    reconciliation["Collection_Rate_Pct"] = np.where(
        reconciliation["Invoice_Amount"] > 0,
        np.round((reconciliation["Total_Paid"] / reconciliation["Invoice_Amount"]) * 100, 2),
        0.0
    )

    # Payment Status
    reconciliation["Payment_Status"] = "Unpaid"
    reconciliation.loc[
        reconciliation["Total_Paid"] >= reconciliation["Invoice_Amount"],
        "Payment_Status"
    ] = "Paid"
    reconciliation.loc[
        (reconciliation["Total_Paid"] > 0) &
        (reconciliation["Total_Paid"] < reconciliation["Invoice_Amount"]),
        "Payment_Status"
    ] = "Partially Paid"

    # Days Overdue and Late Payment Flag Calculation
    # For Unpaid or Partially Paid: Days from Due_Date to AS_OF_DATE (if past due)
    # For Paid: Days overdue is 0; Late flag is Yes if Latest_Payment_Date > Due_Date
    days_overdue_list = []
    late_flag_list = []
    aging_buckets = []

    for _, row in reconciliation.iterrows():
        status = row["Payment_Status"]
        due_d = row["Due_Date"]
        pay_d = row["Latest_Payment_Date"]

        if status == "Paid":
            days_overdue_list.append(0)
            if pd.notna(pay_d) and pay_d > due_d:
                late_flag_list.append("Yes")
            else:
                late_flag_list.append("No")
            aging_buckets.append("Settled / Not Due")

        elif status in ["Unpaid", "Partially Paid"]:
            if AS_OF_DATE > due_d:
                diff = (AS_OF_DATE - due_d).days
                days_overdue_list.append(diff)
                late_flag_list.append("Yes")
                if diff <= 30:
                    aging_buckets.append("1-30 Days")
                elif diff <= 60:
                    aging_buckets.append("31-60 Days")
                elif diff <= 90:
                    aging_buckets.append("61-90 Days")
                else:
                    aging_buckets.append("90+ Days")
            else:
                days_overdue_list.append(0)
                late_flag_list.append("No")
                aging_buckets.append("Current / Not Due")

    reconciliation["Days_Overdue"] = days_overdue_list
    reconciliation["Late_Payment_Flag"] = late_flag_list
    reconciliation["Aging_Bucket"] = aging_buckets

    # Sort predictably by Invoice_Date and Invoice_ID
    reconciliation = reconciliation.sort_values(by=["Invoice_Date", "Invoice_ID"]).reset_index(drop=True)

    # Clean date strings for CSV export
    reconciliation["Invoice_Date"] = reconciliation["Invoice_Date"].dt.strftime("%Y-%m-%d")
    reconciliation["Due_Date"] = reconciliation["Due_Date"].dt.strftime("%Y-%m-%d")
    reconciliation["Latest_Payment_Date"] = reconciliation["Latest_Payment_Date"].dt.strftime("%Y-%m-%d").fillna("")

    df_pay_clean = df_pay.copy()
    df_pay_clean["Payment_Date"] = df_pay_clean["Payment_Date"].dt.strftime("%Y-%m-%d")

    # 7. Audit Summary & Console Metrics
    total_inv_amt = reconciliation["Invoice_Amount"].sum()
    total_paid_amt = reconciliation["Total_Paid"].sum()
    total_out_amt = reconciliation["Outstanding_Amount"].sum()
    overall_rate = (total_paid_amt / total_inv_amt * 100) if total_inv_amt > 0 else 0
    status_counts = reconciliation["Payment_Status"].value_counts().to_dict()
    overdue_count = (reconciliation["Days_Overdue"] > 0).sum()

    print("\n" + "=" * 60)
    print(">> RECONCILIATION SUMMARY AUDIT")
    print("=" * 60)
    print(f"Total Invoices Processed : {len(reconciliation):,}")
    print(f"Total Invoiced Amount    : ${total_inv_amt:,.2f}")
    print(f"Total Collected Amount   : ${total_paid_amt:,.2f}")
    print(f"Total Outstanding Balance: ${total_out_amt:,.2f}")
    print(f"Portfolio Collection Rate: {overall_rate:.2f}%")
    print(f"Status Breakdown         : {status_counts}")
    print(f"Overdue Invoices (>0 d)  : {overdue_count} ({overdue_count/len(reconciliation)*100:.1f}%)")
    print("=" * 60)

    # 8. Export Files
    os.makedirs(output_dir, exist_ok=True)
    proc_recon_path = os.path.join(output_dir, "reconciled_invoices.csv")
    proc_pay_path = os.path.join(output_dir, "cleaned_payments.csv")
    root_recon_path = "reconciled_invoices.csv"
    audit_path = os.path.join(output_dir, "reconciliation_audit.json")

    reconciliation.to_csv(proc_recon_path, index=False)
    reconciliation.to_csv(root_recon_path, index=False)
    df_pay_clean.to_csv(proc_pay_path, index=False)

    audit_log.update({
        "clean_invoice_count": len(reconciliation),
        "clean_payment_count": len(df_pay_clean),
        "total_invoiced": float(total_inv_amt),
        "total_collected": float(total_paid_amt),
        "total_outstanding": float(total_out_amt),
        "collection_rate_pct": float(round(overall_rate, 2)),
        "status_breakdown": status_counts,
        "overdue_invoice_count": int(overdue_count)
    })

    with open(audit_path, "w") as f:
        json.dump(audit_log, f, indent=2)

    print(f">> Successfully exported:")
    print(f"   -> {proc_recon_path}")
    print(f"   -> {proc_pay_path}")
    print(f"   -> {root_recon_path}")
    print(f"   -> {audit_path}")

    return reconciliation, df_pay_clean

if __name__ == "__main__":
    clean_and_reconcile()

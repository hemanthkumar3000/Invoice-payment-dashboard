"""
generate_synthetic_data.py
--------------------------
Generates realistic synthetic B2B finance datasets:
  - invoices.csv (250 records)
  - payments.csv (300+ payment records)

Features:
  - Fully paid, partially paid, and unpaid invoices
  - Single and multi-tranche payments
  - On-time and overdue payments
  - Controlled dirty data anomalies (duplicates, trailing whitespaces,
    inconsistent date strings, missing payment amounts) for data cleaning validation.

Note: Marked explicitly as synthetic finance data per consulting project requirements.
"""

import os
import random
import datetime
import numpy as np
import pandas as pd

# Set deterministic seed for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

def generate_datasets(output_dirs):
    print(">> Generating synthetic invoice and payment datasets...")

    departments = ["Sales", "Services", "Consulting", "IT Support", "Operations", "Marketing"]
    customers = [
        "ABC Retail",
        "XYZ Traders",
        "Apex Logistics",
        "Global Tech Solutions",
        "Summit Healthcare",
        "Horizon Energy",
        "Pinnacle Media",
        "Nexus Manufacturing",
        "Quantum Dynamics",
        "Vanguard Distribution",
        "BlueSky Consulting",
        "Starlight Hospitality",
        "Metro Foods Corp",
        "Evergreen Agrotech",
        "Titan Industrial",
        "Beacon Financial",
        "Sterling Automotive",
        "Oasis Pharmaceuticals",
        "Crestline Software",
        "Orion Aerospace"
    ]
    payment_methods = ["Bank Transfer", "UPI", "Credit Card", "ACH", "Cheque"]

    num_invoices = 250
    start_date = datetime.date(2026, 1, 1)
    end_date = datetime.date(2026, 9, 15)
    days_range = (end_date - start_date).days

    invoices = []
    payments = []
    payment_counter = 1

    for i in range(1, num_invoices + 1):
        inv_id = f"INV{i:04d}"
        cust = random.choice(customers)
        dept = random.choice(departments)
        
        # Realistic invoice amount between 5,000 and 100,000
        amount = int(random.choice(range(5000, 105000, 2500)))

        # Invoice date distributed across Jan - Sep 2026
        inv_day_offset = random.randint(0, days_range)
        inv_date = start_date + datetime.timedelta(days=inv_day_offset)

        # Standard credit terms: Net 30, Net 45, or Net 60
        credit_term = random.choice([30, 45, 60])
        due_date = inv_date + datetime.timedelta(days=credit_term)

        # Payment behaviors:
        # 55% Fully Paid (some on time, some late, some split tranches)
        # 25% Partially Paid
        # 20% Unpaid
        scenario_roll = random.random()

        if scenario_roll < 0.55:
            # Fully Paid
            is_split = random.random() < 0.25  # 25% split into 2 installments
            is_late = random.random() < 0.25   # 25% paid after due date

            if not is_split:
                if is_late:
                    pay_delay = random.randint(3, 40)
                    pay_date = due_date + datetime.timedelta(days=pay_delay)
                else:
                    pay_offset = random.randint(5, credit_term - 1)
                    pay_date = inv_date + datetime.timedelta(days=pay_offset)
                
                pay_id = f"PAY{payment_counter:05d}"
                payment_counter += 1
                payments.append({
                    "Payment_ID": pay_id,
                    "Invoice_ID": inv_id,
                    "Payment_Date": pay_date.strftime("%Y-%m-%d"),
                    "Payment_Amount": float(amount),
                    "Payment_Method": random.choice(payment_methods)
                })
            else:
                # Two payments summing to full amount
                part1 = int(round((amount * random.uniform(0.3, 0.6)) / 500) * 500)
                part2 = amount - part1
                
                pay_date_1 = inv_date + datetime.timedelta(days=random.randint(5, 20))
                pay_id_1 = f"PAY{payment_counter:05d}"
                payment_counter += 1
                payments.append({
                    "Payment_ID": pay_id_1,
                    "Invoice_ID": inv_id,
                    "Payment_Date": pay_date_1.strftime("%Y-%m-%d"),
                    "Payment_Amount": float(part1),
                    "Payment_Method": random.choice(payment_methods)
                })

                if is_late:
                    pay_date_2 = due_date + datetime.timedelta(days=random.randint(5, 30))
                else:
                    pay_date_2 = due_date - datetime.timedelta(days=random.randint(1, 10))
                
                pay_id_2 = f"PAY{payment_counter:05d}"
                payment_counter += 1
                payments.append({
                    "Payment_ID": pay_id_2,
                    "Invoice_ID": inv_id,
                    "Payment_Date": pay_date_2.strftime("%Y-%m-%d"),
                    "Payment_Amount": float(part2),
                    "Payment_Method": random.choice(payment_methods)
                })

        elif scenario_roll < 0.80:
            # Partially Paid
            # Partial amount is 20% to 75% of invoice amount
            pct_paid = random.uniform(0.20, 0.75)
            partial_amount = int(round((amount * pct_paid) / 500) * 500)
            if partial_amount >= amount:
                partial_amount = amount - 1000

            pay_offset = random.randint(5, credit_term + 15)
            pay_date = inv_date + datetime.timedelta(days=pay_offset)
            pay_id = f"PAY{payment_counter:05d}"
            payment_counter += 1
            payments.append({
                "Payment_ID": pay_id,
                "Invoice_ID": inv_id,
                "Payment_Date": pay_date.strftime("%Y-%m-%d"),
                "Payment_Amount": float(partial_amount),
                "Payment_Method": random.choice(payment_methods)
            })

        else:
            # Unpaid - no payment records created
            pass

        invoices.append({
            "Invoice_ID": inv_id,
            "Customer": cust,
            "Invoice_Date": inv_date.strftime("%Y-%m-%d"),
            "Due_Date": due_date.strftime("%Y-%m-%d"),
            "Invoice_Amount": float(amount),
            "Department": dept
        })

    df_invoices = pd.DataFrame(invoices)
    df_payments = pd.DataFrame(payments)

    # -------------------------------------------------------------
    # Inject Controlled Real-World Data Quality Anomalies to Clean:
    # -------------------------------------------------------------
    print(f">> Initial counts: {len(df_invoices)} invoices, {len(df_payments)} payments")
    
    # 1. Duplicate records (3 duplicate invoices and 3 duplicate payments)
    dupe_invoices = df_invoices.iloc[[10, 45, 120]].copy()
    df_invoices = pd.concat([df_invoices, dupe_invoices], ignore_index=True)

    dupe_payments = df_payments.iloc[[15, 60, 110]].copy()
    df_payments = pd.concat([df_payments, dupe_payments], ignore_index=True)

    # 2. Leading/trailing whitespace in Customer names (5 rows)
    for idx in [5, 22, 70, 130, 180]:
        if idx < len(df_invoices):
            df_invoices.loc[idx, "Customer"] = f"  {df_invoices.loc[idx, 'Customer']}  "

    # 3. Inconsistent date formats in a few rows (e.g. MM/DD/YYYY)
    for idx in [8, 50, 140]:
        if idx < len(df_invoices):
            d = datetime.datetime.strptime(df_invoices.loc[idx, "Invoice_Date"], "%Y-%m-%d")
            df_invoices.loc[idx, "Invoice_Date"] = d.strftime("%m/%d/%Y")

    for idx in [12, 65, 125]:
        if idx < len(df_payments):
            d = datetime.datetime.strptime(df_payments.loc[idx, "Payment_Date"], "%Y-%m-%d")
            df_payments.loc[idx, "Payment_Date"] = d.strftime("%m/%d/%Y")

    # 4. Missing/null values in payment amounts (2 rows) and payment method (1 row)
    df_payments.loc[30, "Payment_Amount"] = np.nan
    df_payments.loc[85, "Payment_Amount"] = np.nan
    df_payments.loc[42, "Payment_Method"] = np.nan

    print(f">> After anomaly injection: {len(df_invoices)} invoices, {len(df_payments)} payments")

    # Save to requested destinations
    for out_dir in output_dirs:
        os.makedirs(out_dir, exist_ok=True)
        inv_path = os.path.join(out_dir, "invoices.csv")
        pay_path = os.path.join(out_dir, "payments.csv")
        df_invoices.to_csv(inv_path, index=False)
        df_payments.to_csv(pay_path, index=False)
        print(f"   Saved -> {inv_path}")
        print(f"   Saved -> {pay_path}")

    return df_invoices, df_payments

if __name__ == "__main__":
    dirs = [
        os.path.join("data", "raw"),
        "."  # root directory as well
    ]
    generate_datasets(dirs)
    print(">> Synthetic data generation complete.")

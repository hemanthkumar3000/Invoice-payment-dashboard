"""
test_reconciliation.py
----------------------
Unit and data-integrity tests for the Invoice-Payment Reconciliation pipeline.
Run with: pytest tests/test_reconciliation.py
"""

import os
import pytest
import pandas as pd
import numpy as np

RECON_CSV = "data/processed/reconciled_invoices.csv"
CLEAN_PAY_CSV = "data/processed/cleaned_payments.csv"

@pytest.fixture(scope="module")
def recon_df():
    assert os.path.exists(RECON_CSV), f"Missing {RECON_CSV}"
    df = pd.read_csv(RECON_CSV)
    return df

@pytest.fixture(scope="module")
def pay_df():
    assert os.path.exists(CLEAN_PAY_CSV), f"Missing {CLEAN_PAY_CSV}"
    df = pd.read_csv(CLEAN_PAY_CSV)
    return df

def test_invoice_deduplication(recon_df):
    """All invoices in reconciled dataset must have unique IDs."""
    assert recon_df["Invoice_ID"].is_unique, "Duplicate Invoice_IDs found in reconciled dataset!"
    assert len(recon_df) == 250, f"Expected 250 invoices, found {len(recon_df)}"

def test_payment_deduplication(pay_df):
    """All payments in clean payment dataset must have unique IDs."""
    assert pay_df["Payment_ID"].is_unique, "Duplicate Payment_IDs found in cleaned payments dataset!"

def test_accounting_invariant_equation(recon_df):
    """
    Fundamental accounting identity:
    Invoice_Amount must equal Total_Paid + Outstanding_Amount (for non-overpayments).
    """
    diff = np.abs(recon_df["Invoice_Amount"] - (recon_df["Total_Paid"] + recon_df["Outstanding_Amount"]))
    assert (diff < 0.01).all(), f"Accounting identity failed for { (diff >= 0.01).sum() } records!"

def test_no_negative_balances(recon_df):
    """No invoice should have a negative outstanding balance."""
    assert (recon_df["Outstanding_Amount"] >= 0).all(), "Negative outstanding balances detected!"

def test_payment_status_logic(recon_df):
    """Ensure status aligns strictly with payment vs invoice amounts."""
    paid_mask = recon_df["Total_Paid"] >= recon_df["Invoice_Amount"]
    assert (recon_df.loc[paid_mask, "Payment_Status"] == "Paid").all(), "Mismatched Paid status"

    partial_mask = (recon_df["Total_Paid"] > 0) & (recon_df["Total_Paid"] < recon_df["Invoice_Amount"])
    assert (recon_df.loc[partial_mask, "Payment_Status"] == "Partially Paid").all(), "Mismatched Partially Paid status"

    unpaid_mask = recon_df["Total_Paid"] == 0
    assert (recon_df.loc[unpaid_mask, "Payment_Status"] == "Unpaid").all(), "Mismatched Unpaid status"

def test_overdue_invariants(recon_df):
    """Paid invoices must have Days_Overdue == 0."""
    paid_overdue = recon_df.loc[recon_df["Payment_Status"] == "Paid", "Days_Overdue"]
    assert (paid_overdue == 0).all(), "Paid invoices have non-zero Days_Overdue!"

def test_cash_reconciliation_total(recon_df, pay_df):
    """Total cash accounted in reconciled table must equal total payment cash for matched invoices."""
    recon_total_cash = recon_df["Total_Paid"].sum()
    pay_total_cash = pay_df.loc[pay_df["Invoice_ID"].isin(recon_df["Invoice_ID"]), "Payment_Amount"].sum()
    assert abs(recon_total_cash - pay_total_cash) < 0.01, f"Cash mismatch: Recon ${recon_total_cash:,.2f} vs Pay ${pay_total_cash:,.2f}"

def test_valid_departments(recon_df):
    """Check that departments belong to expected set."""
    expected_depts = {"Sales", "Services", "Consulting", "IT Support", "Operations", "Marketing"}
    actual_depts = set(recon_df["Department"].unique())
    assert actual_depts.issubset(expected_depts), f"Unexpected department detected: {actual_depts - expected_depts}"

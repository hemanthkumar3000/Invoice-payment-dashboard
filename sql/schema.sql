-- ====================================================================
-- SCHEMA: Finance Reconciliation Database
-- ====================================================================

DROP TABLE IF EXISTS raw_invoices;
CREATE TABLE raw_invoices (
    Invoice_ID TEXT PRIMARY KEY,
    Customer TEXT NOT NULL,
    Invoice_Date DATE NOT NULL,
    Due_Date DATE NOT NULL,
    Invoice_Amount REAL NOT NULL,
    Department TEXT NOT NULL
);

DROP TABLE IF EXISTS raw_payments;
CREATE TABLE raw_payments (
    Payment_ID TEXT PRIMARY KEY,
    Invoice_ID TEXT NOT NULL,
    Payment_Date DATE NOT NULL,
    Payment_Amount REAL NOT NULL,
    Payment_Method TEXT
);

DROP TABLE IF EXISTS reconciled_invoices;
CREATE TABLE reconciled_invoices (
    Invoice_ID TEXT PRIMARY KEY,
    Customer TEXT NOT NULL,
    Invoice_Date DATE NOT NULL,
    Due_Date DATE NOT NULL,
    Invoice_Amount REAL NOT NULL,
    Department TEXT NOT NULL,
    Total_Paid REAL NOT NULL,
    Payment_Count INTEGER NOT NULL,
    Latest_Payment_Date DATE,
    Payment_Methods TEXT,
    Outstanding_Amount REAL NOT NULL,
    Collection_Rate_Pct REAL NOT NULL,
    Payment_Status TEXT NOT NULL,
    Days_Overdue INTEGER NOT NULL,
    Late_Payment_Flag TEXT NOT NULL,
    Aging_Bucket TEXT NOT NULL
);

-- Indices for reporting performance
CREATE INDEX IF NOT EXISTS idx_recon_dept ON reconciled_invoices(Department);
CREATE INDEX IF NOT EXISTS idx_recon_cust ON reconciled_invoices(Customer);
CREATE INDEX IF NOT EXISTS idx_recon_status ON reconciled_invoices(Payment_Status);
CREATE INDEX IF NOT EXISTS idx_recon_dates ON reconciled_invoices(Invoice_Date, Due_Date);

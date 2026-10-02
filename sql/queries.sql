-- ====================================================================
-- INVOICE-PAYMENT RECONCILIATION SQL QUERIES
-- ====================================================================

-- --------------------------------------------------------------------
-- Query 1: Revenue, Payments, and Outstanding Balance by Department
-- (Core Consulting Requirement)
-- --------------------------------------------------------------------
SELECT
    Department,
    COUNT(*) AS total_invoices,
    ROUND(SUM(Invoice_Amount), 2) AS invoiced_amount,
    ROUND(SUM(Total_Paid), 2) AS collected_amount,
    ROUND(SUM(Outstanding_Amount), 2) AS outstanding_amount,
    ROUND((SUM(Total_Paid) / SUM(Invoice_Amount)) * 100, 2) AS collection_rate_pct
FROM reconciled_invoices
GROUP BY Department
ORDER BY outstanding_amount DESC;


-- --------------------------------------------------------------------
-- Query 2: Top 10 Customers with Largest Unpaid Balances
-- (Credit Risk & Exposure Analysis)
-- --------------------------------------------------------------------
SELECT
    Customer,
    COUNT(*) AS total_invoices,
    ROUND(SUM(Invoice_Amount), 2) AS total_invoiced,
    ROUND(SUM(Total_Paid), 2) AS total_collected,
    ROUND(SUM(Outstanding_Amount), 2) AS total_outstanding,
    ROUND((SUM(Total_Paid) / SUM(Invoice_Amount)) * 100, 2) AS collection_rate_pct,
    MAX(Days_Overdue) AS max_days_overdue
FROM reconciled_invoices
WHERE Outstanding_Amount > 0
GROUP BY Customer
ORDER BY total_outstanding DESC
LIMIT 10;


-- --------------------------------------------------------------------
-- Query 3: Payment Status Summary
-- (Fulfillment & Cash Flow Health)
-- --------------------------------------------------------------------
SELECT
    Payment_Status,
    COUNT(*) AS invoice_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reconciled_invoices), 2) AS pct_of_invoices,
    ROUND(SUM(Invoice_Amount), 2) AS invoice_value,
    ROUND(SUM(Total_Paid), 2) AS collected_value,
    ROUND(SUM(Outstanding_Amount), 2) AS outstanding_value,
    ROUND(AVG(Days_Overdue), 1) AS avg_days_overdue
FROM reconciled_invoices
GROUP BY Payment_Status
ORDER BY invoice_value DESC;


-- --------------------------------------------------------------------
-- Query 4: Accounts Receivable Aging Analysis
-- (Delinquency Bucketing)
-- --------------------------------------------------------------------
SELECT
    Aging_Bucket,
    COUNT(*) AS invoice_count,
    ROUND(SUM(Outstanding_Amount), 2) AS outstanding_balance,
    ROUND(SUM(Outstanding_Amount) * 100.0 / (SELECT SUM(Outstanding_Amount) FROM reconciled_invoices), 2) AS pct_of_total_ar,
    ROUND(AVG(Days_Overdue), 1) AS avg_days_overdue
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


-- --------------------------------------------------------------------
-- Query 5: Monthly Invoicing vs Collection Velocity
-- (Cash Flow Trend Analysis)
-- --------------------------------------------------------------------
SELECT
    SUBSTR(Invoice_Date, 1, 7) AS invoice_month,
    COUNT(*) AS invoices_issued,
    ROUND(SUM(Invoice_Amount), 2) AS monthly_invoiced,
    ROUND(SUM(Total_Paid), 2) AS monthly_collected,
    ROUND(SUM(Outstanding_Amount), 2) AS monthly_outstanding,
    ROUND((SUM(Total_Paid) / SUM(Invoice_Amount)) * 100, 2) AS collection_efficiency_pct
FROM reconciled_invoices
GROUP BY SUBSTR(Invoice_Date, 1, 7)
ORDER BY invoice_month ASC;


-- --------------------------------------------------------------------
-- Query 6: Late Payment Distribution by Department
-- (Operational Performance Bottlenecks)
-- --------------------------------------------------------------------
SELECT
    Department,
    COUNT(*) AS total_invoices,
    SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1 ELSE 0 END) AS late_invoices_count,
    ROUND(SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS late_rate_pct,
    ROUND(AVG(CASE WHEN Days_Overdue > 0 THEN Days_Overdue ELSE NULL END), 1) AS avg_days_overdue_when_late
FROM reconciled_invoices
GROUP BY Department
ORDER BY late_rate_pct DESC;


-- --------------------------------------------------------------------
-- Query 7: Reconciled vs Raw Payment Integrity Validation
-- (Consulting Audit Check: Matching Subledger to Ledger)
-- --------------------------------------------------------------------
SELECT
    'Raw Payments Table' AS source,
    COUNT(DISTINCT Invoice_ID) AS unique_invoices_with_payments,
    ROUND(SUM(Payment_Amount), 2) AS total_cash_received
FROM raw_payments
UNION ALL
SELECT
    'Reconciled Invoices Table' AS source,
    COUNT(DISTINCT Invoice_ID) AS unique_invoices_with_payments,
    ROUND(SUM(Total_Paid), 2) AS total_cash_received
FROM reconciled_invoices
WHERE Total_Paid > 0;

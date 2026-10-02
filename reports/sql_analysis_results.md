# SQL Financial Analysis & Reconciliation Report
**Generated On:** 2026-10-02 16:21:09
**Database:** SQLite (`finance_reconciliation.db`)

---

### 1. Department Revenue, Collections & Outstanding Balances
```sql
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
        ```
| Department   |   Total_Invoices | Invoiced_Amount   | Collected_Amount   | Outstanding_Amount   | Collection_Rate   |
|:-------------|-----------------:|:------------------|:-------------------|:---------------------|:------------------|
| Services     |               51 | $3,012,500.00     | $1,715,500.00      | $1,297,000.00        | 56.95%            |
| Operations   |               34 | $1,872,500.00     | $984,500.00        | $888,000.00          | 52.58%            |
| Marketing    |               44 | $2,180,000.00     | $1,395,000.00      | $785,000.00          | 63.99%            |
| IT Support   |               48 | $2,520,000.00     | $1,805,000.00      | $715,000.00          | 71.63%            |
| Consulting   |               36 | $2,095,000.00     | $1,445,500.00      | $649,500.00          | 69.0%             |
| Sales        |               37 | $1,920,000.00     | $1,405,000.00      | $515,000.00          | 73.18%            |

### 2. Top 10 Customers with Largest Outstanding Balances
```sql
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
        ```
| Customer              |   Invoices | Invoiced    | Collected   | Total_Outstanding   | Collection_Rate   |   Max_Days_Overdue |
|:----------------------|-----------:|:------------|:------------|:--------------------|:------------------|-------------------:|
| Vanguard Distribution |         13 | $770,000.00 | $137,000.00 | $633,000.00         | 17.79%            |                225 |
| Beacon Financial      |          7 | $487,500.00 | $99,500.00  | $388,000.00         | 20.41%            |                232 |
| BlueSky Consulting    |          7 | $460,000.00 | $78,500.00  | $381,500.00         | 17.07%            |                210 |
| Apex Logistics        |         12 | $542,500.00 | $182,000.00 | $360,500.00         | 33.55%            |                203 |
| Nexus Manufacturing   |          7 | $475,000.00 | $154,000.00 | $321,000.00         | 32.42%            |                163 |
| Pinnacle Media        |          6 | $435,000.00 | $138,000.00 | $297,000.00         | 31.72%            |                213 |
| Quantum Dynamics      |          9 | $405,000.00 | $111,500.00 | $293,500.00         | 27.53%            |                185 |
| Oasis Pharmaceuticals |          5 | $287,500.00 | $29,000.00  | $258,500.00         | 10.09%            |                215 |
| Metro Foods Corp      |          5 | $347,500.00 | $114,000.00 | $233,500.00         | 32.81%            |                197 |
| Horizon Energy        |          4 | $352,500.00 | $120,500.00 | $232,000.00         | 34.18%            |                231 |

### 3. Payment Status & Cash Fulfillment Distribution
```sql
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
        ```
| Payment_Status   |   Invoice_Count | Pct_Volume   | Invoiced_Value   | Collected_Value   | Outstanding_Value   |   Avg_Days_Overdue |
|:-----------------|----------------:|:-------------|:-----------------|:------------------|:--------------------|-------------------:|
| Paid             |             128 | 51.2%        | $6,805,000.00    | $6,805,000.00     | $0.00               |                0   |
| Partially Paid   |              65 | 26.0%        | $3,715,000.00    | $1,945,500.00     | $1,769,500.00       |               79.6 |
| Unpaid           |              57 | 22.8%        | $3,080,000.00    | $0.00             | $3,080,000.00       |               95.7 |

### 4. Accounts Receivable Aging Breakdown (Delinquency Risk)
```sql
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
        ```
| Aging_Bucket      |   Overdue_Count | Outstanding_Balance   | Pct_Of_Total_AR   |   Avg_Days_Overdue |
|:------------------|----------------:|:----------------------|:------------------|-------------------:|
| 1-30 Days         |              22 | $688,000.00           | 14.2%             |               15.1 |
| 31-60 Days        |              18 | $676,000.00           | 13.9%             |               43.2 |
| 61-90 Days        |              14 | $562,500.00           | 11.6%             |               71.5 |
| 90+ Days          |              51 | $2,222,500.00         | 45.8%             |              166.9 |
| Current / Not Due |              17 | $700,500.00           | 14.4%             |                0   |

### 5. Monthly Invoiced vs Collected Cash Velocity
```sql
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
        ```
| Month   |   Invoices | Invoiced      | Collected     | Outstanding   | Velocity_Rate   |
|:--------|-----------:|:--------------|:--------------|:--------------|:----------------|
| 2026-01 |         28 | $1,725,000.00 | $819,000.00   | $906,000.00   | 47.5%           |
| 2026-02 |         26 | $1,580,000.00 | $1,184,000.00 | $396,000.00   | 74.9%           |
| 2026-03 |         25 | $1,095,000.00 | $845,000.00   | $250,000.00   | 77.2%           |
| 2026-04 |         22 | $1,340,000.00 | $1,008,500.00 | $331,500.00   | 75.3%           |
| 2026-05 |         33 | $1,565,000.00 | $972,000.00   | $593,000.00   | 62.1%           |
| 2026-06 |         32 | $1,852,500.00 | $1,234,000.00 | $618,500.00   | 66.6%           |
| 2026-07 |         33 | $1,712,500.00 | $1,020,500.00 | $692,000.00   | 59.6%           |
| 2026-08 |         36 | $1,860,000.00 | $1,076,000.00 | $784,000.00   | 57.8%           |
| 2026-09 |         15 | $870,000.00   | $591,500.00   | $278,500.00   | 68.0%           |

### 6. Operational Late Payment Analysis by Department
```sql
            SELECT
                Department,
                COUNT(*) AS Total_Invoices,
                SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1 ELSE 0 END) AS Late_Invoices,
                ROUND(SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) || '%' AS Late_Rate_Pct,
                ROUND(AVG(CASE WHEN Days_Overdue > 0 THEN Days_Overdue ELSE NULL END), 1) AS Avg_Days_Late
            FROM reconciled_invoices
            GROUP BY Department
            ORDER BY SUM(CASE WHEN Late_Payment_Flag = 'Yes' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*) DESC;
        ```
| Department   |   Total_Invoices |   Late_Invoices | Late_Rate_Pct   |   Avg_Days_Late |
|:-------------|-----------------:|----------------:|:----------------|----------------:|
| Operations   |               34 |              21 | 61.8%           |            97.6 |
| Services     |               51 |              29 | 56.9%           |           105.9 |
| Marketing    |               44 |              25 | 56.8%           |            72.6 |
| Sales        |               37 |              20 | 54.1%           |            95.5 |
| IT Support   |               48 |              19 | 39.6%           |           113.2 |
| Consulting   |               36 |              14 | 38.9%           |           133.5 |

### 7. Ledger Integrity Verification (Payments vs Invoices)
```sql
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
        ```
| Source                    |   Invoices_With_Payments | Total_Cash_Accounted   |
|:--------------------------|-------------------------:|:-----------------------|
| Raw Payments Subledger    |                      195 | $8,750,500.00          |
| Reconciled General Ledger |                      193 | $8,750,500.00          |

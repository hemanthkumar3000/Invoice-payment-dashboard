# Power BI One-Page Dashboard Setup Guide
## Project: Invoice–Payment Reconciliation & Revenue KPI Dashboard

This guide walks you through creating the **single-page executive reconciliation dashboard** in Microsoft Power BI Desktop using `reconciled_invoices.csv`.

---

## 1. Canvas Settings & Theme
1. **Open Power BI Desktop**.
2. Go to **View** -> **Themes** -> Select **Executive** or **Classic Dark/Light**.
3. Set Canvas size:
   - Format Page -> **Canvas Settings** -> Type: **16:9** (1280 x 720 px or 1920 x 1080 px).
   - Canvas Background: Color `#F8FAFC` (Slate 50), Transparency `0%`.

---

## 2. Ingest the Data
### Option A: Direct CSV Import (Recommended - 1 Click)
1. Click **Home** -> **Get Data** -> **Text/CSV**.
2. Select `data/processed/reconciled_invoices.csv` (or the root `reconciled_invoices.csv`).
3. Click **Load**.
4. Rename table to `ReconciledInvoices`.

### Option B: Power Query M Script
If you want to demonstrate raw ETL transformation inside Power BI:
1. Click **Home** -> **Transform data** -> Open Power Query Editor.
2. Click **New Source** -> **Blank Query** -> **Advanced Editor**.
3. Paste the contents of `power_bi/PowerQuery_M_Script.m`.
4. Click **Done** -> **Close & Apply**.

---

## 3. Create DAX Measures
Create a dedicated measures table or add the measures from `power_bi/DAX_Measures.dax` directly to `ReconciledInvoices`:

| Measure Name | DAX Formula | Format |
|---|---|---|
| **Total Invoiced Amount** | `SUM(ReconciledInvoices[Invoice_Amount])` | Currency (`$#,##0`) |
| **Total Collected Amount** | `SUM(ReconciledInvoices[Total_Paid])` | Currency (`$#,##0`) |
| **Total Outstanding Amount** | `SUM(ReconciledInvoices[Outstanding_Amount])` | Currency (`$#,##0`) |
| **Collection Rate %** | `DIVIDE([Total Collected Amount], [Total Invoiced Amount], 0)` | Percentage (`0.0%`) |
| **Number of Overdue Invoices**| `CALCULATE(COUNTROWS(ReconciledInvoices), ReconciledInvoices[Payment_Status] <> "Paid", ReconciledInvoices[Days_Overdue] > 0)` | Whole Number (`#,##0`) |

---

## 4. Visual Layout Specification (One-Page Dashboard)

### Top Header Bar (Y: 10, Height: 60)
- **Text Box**: 
  - Title: `INVOICE–PAYMENT RECONCILIATION & REVENUE DASHBOARD` (Font: Segoe UI Bold 18pt, Color `#0F172A`)
  - Subtitle: `Cross-System Financial Intelligence | Snapshot As-Of: 2026-10-01` (Font: Segoe UI Regular 10pt, Color `#64748B`)

---

### Row 1: KPI Cards (Y: 80, Height: 90)
Arrange 5 Card visuals horizontally across the top:

1. **Card 1 (Total Invoiced)**:
   - Field: `[Total Invoiced Amount]`
   - Callout Value: 24pt Bold, Color `#1E293B`
   - Label: "Total Invoiced"
2. **Card 2 (Total Collected)**:
   - Field: `[Total Collected Amount]`
   - Callout Value: 24pt Bold, Color `#059669` (Emerald)
   - Label: "Total Collected"
3. **Card 3 (Total Outstanding)**:
   - Field: `[Total Outstanding Amount]`
   - Callout Value: 24pt Bold, Color `#DC2626` (Red)
   - Label: "Total Outstanding"
4. **Card 4 (Collection Rate %)**:
   - Field: `[Collection Rate %]`
   - Callout Value: 24pt Bold, Color `#D97706` (Amber)
   - Label: "Collection Rate %"
5. **Card 5 (Overdue Invoices)**:
   - Field: `[Number of Overdue Invoices]`
   - Callout Value: 24pt Bold, Color `#E11D48` (Rose)
   - Label: "Overdue Invoices"

---

### Row 2: Slicers / Interactive Filters (Y: 180, Height: 60)
Create 4 Slicer visuals side by side:

1. **Department Slicer**:
   - Field: `ReconciledInvoices[Department]`
   - Style: Dropdown / Tile
2. **Customer Slicer**:
   - Field: `ReconciledInvoices[Customer]`
   - Style: Dropdown with search enabled
3. **Payment Status Slicer**:
   - Field: `ReconciledInvoices[Payment_Status]`
   - Style: Tile / Horizontal pills (`Paid`, `Partially Paid`, `Unpaid`)
4. **Invoice Date Slicer**:
   - Field: `ReconciledInvoices[Invoice_Date]`
   - Style: Between (Date Slider)

---

### Row 3: Analytical Charts (Y: 250, Height: 240)
Arrange 4 core charts:

1. **Chart 1: Bar Chart — Outstanding Amount by Customer (Top Debtors)**
   - Visual Type: Clustered Bar Chart (Horizontal)
   - Y-Axis: `ReconciledInvoices[Customer]`
   - X-Axis: `[Total Outstanding Amount]`
   - Filter on Visual: Top 10 by `[Total Outstanding Amount]`
   - Color: Coral Red (`#EF4444`)
   - Data Labels: On (Currency formatted `$#,##0`)

2. **Chart 2: Donut Chart — Invoice Status Distribution**
   - Visual Type: Donut Chart
   - Legend: `ReconciledInvoices[Payment_Status]`
   - Values: `[Total Invoiced Amount]` or `COUNT(Invoice_ID)`
   - Colors:
     - `Paid`: `#10B981` (Green)
     - `Partially Paid`: `#F59E0B` (Amber)
     - `Unpaid`: `#EF4444` (Red)

3. **Chart 3: Line Chart — Monthly Invoiced vs Collected Amount**
   - Visual Type: Line Chart
   - X-Axis: `Invoice_Date` (Hierarchy: Year, Month)
   - Y-Axis:
     - Line 1: `[Total Invoiced Amount]` (Deep Slate `#3B82F6`)
     - Line 2: `[Total Collected Amount]` (Emerald `#10B981`)
   - Markers: On
   - Tooltips: `[Collection Rate %]`

4. **Chart 4: Bar Chart — Outstanding Amount by Department**
   - Visual Type: Clustered Column Chart (Vertical)
   - X-Axis: `ReconciledInvoices[Department]`
   - Y-Axis: `[Total Outstanding Amount]`
   - Sort By: `[Total Outstanding Amount]` Descending
   - Color: Indigo / Navy (`#6366F1`)

---

### Row 4: Detail Transaction Table (Y: 500, Height: 200)
- Visual Type: **Table**
- Fields:
  1. `Invoice_ID`
  2. `Customer`
  3. `Due_Date`
  4. `Invoice_Amount` (Format: `$#,##0.00`)
  5. `Total_Paid` (Format: `$#,##0.00`)
  6. `Outstanding_Amount` (Format: `$#,##0.00`)
  7. `Payment_Status`
  8. `Days_Overdue`
- Conditional Formatting in Table:
  - Select column `Payment_Status` -> Conditional formatting -> Background color:
    - Rule: If value is `"Paid"` then `#D1FAE5` (Light green)
    - Rule: If value is `"Partially Paid"` then `#FEF3C7` (Light yellow)
    - Rule: If value is `"Unpaid"` then `#FEE2E2` (Light red)
  - Select column `Days_Overdue` -> Conditional formatting -> Font color:
    - If value > 0 then `#B91C1C` (Bold Red)

---

## 5. Visual Specification Summary (Checklist)
- [x] 1-Page Layout constraint respected
- [x] All 5 KPI cards present and formatted
- [x] 4 Required Visuals + Monthly Trend line chart configured
- [x] All 4 Slicers (Department, Customer, Payment Status, Date) active
- [x] Detail table formatted with conditional color codes

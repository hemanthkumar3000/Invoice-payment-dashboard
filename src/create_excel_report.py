"""
create_excel_report.py
----------------------
Builds a professional executive financial reconciliation workbook in Excel:
  - File: reports/reconciliation_report.xlsx & reconciliation_report.xlsx
  - Sheets:
      1. Executive Dashboard (KPI cards, Department & Aging summary tables)
      2. Reconciled Data Master (with Conditional Formatting: Green=Paid, Yellow=Partially Paid, Red=Unpaid/Overdue)
      3. Pivot_Customer_Outstanding (Summary & pivot view of customer debt)
      4. Pivot_Dept_Invoice_Amount (Summary & pivot view of department volume)
      5. Aging_Analysis (AR aging schedule)
"""

import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule

RECON_CSV = "data/processed/reconciled_invoices.csv"
OUTPUT_PATHS = [
    "reports/reconciliation_report.xlsx",
    "reconciliation_report.xlsx"
]

def format_cell(cell, font=None, fill=None, alignment=None, border=None, number_format=None):
    if font: cell.font = font
    if fill: cell.fill = fill
    if alignment: cell.alignment = alignment
    if border: cell.border = border
    if number_format: cell.number_format = number_format

def auto_fit_columns(ws, min_width=12, max_width=32):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            if cell.number_format and "$" in cell.number_format:
                val_str = val_str + "    "  # extra breathing room for currency
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_width), max_width)

def generate_excel_report():
    print(">> Generating Executive Excel Reconciliation Workbook...")
    df = pd.read_csv(RECON_CSV)

    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Theme Palette (Modern Corporate Slate / Navy / Emerald / Amber / Coral)
    navy_header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    dark_blue_sub = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    card_bg_blue = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    card_bg_green = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")
    card_bg_red = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
    card_bg_amber = PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    font_title = Font(name="Segoe UI", size=16, bold=True, color="1E293B")
    font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="64748B")
    font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_sub_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_card_title = Font(name="Segoe UI", size=9, bold=True, color="64748B")
    font_card_val = Font(name="Segoe UI", size=16, bold=True, color="0F172A")
    font_bold = Font(name="Segoe UI", size=10, bold=True, color="1E293B")
    font_regular = Font(name="Segoe UI", size=10, color="1E293B")

    thin_border_side = Side(border_style="thin", color="E2E8F0")
    thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="medium", color="1E293B"), top=Side(border_style="thin", color="E2E8F0"))
    card_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    num_curr = "$#,##0.00"
    num_curr_k = "$#,##0"
    num_pct = "0.0%"
    num_int = "#,##0"

    # =========================================================================
    # SHEET 1: Executive Dashboard
    # =========================================================================
    ws_dash = wb.create_sheet(title="Executive Dashboard")
    ws_dash.views.sheetView[0].showGridLines = True

    # Title Banner
    ws_dash.merge_cells("B2:K2")
    ws_dash["B2"] = "FINANCE EXECUTIVE DASHBOARD: INVOICE-PAYMENT RECONCILIATION"
    ws_dash["B2"].font = font_title
    ws_dash["B2"].alignment = align_left

    ws_dash.merge_cells("B3:K3")
    ws_dash["B3"] = f"Unified Financial Intelligence Layer | Audit Date: 2026-10-01 | Total Portfolio: {len(df)} Invoices"
    ws_dash["B3"].font = font_subtitle
    ws_dash["B3"].alignment = align_left

    # KPI Summary Cards (Row 5 to 7)
    kpi_defs = [
        ("B", "C", "TOTAL INVOICED", f"='Reconciled Master'!E{len(df)+2}", card_bg_blue, num_curr_k),
        ("D", "E", "TOTAL COLLECTED", f"='Reconciled Master'!G{len(df)+2}", card_bg_green, num_curr_k),
        ("F", "G", "OUTSTANDING AR", f"='Reconciled Master'!K{len(df)+2}", card_bg_red, num_curr_k),
        ("H", "I", "COLLECTION RATE", f"=D6/B6", card_bg_amber, num_pct),
        ("J", "K", "OVERDUE INVOICES", f"=COUNTIF('Reconciled Master'!N2:N{len(df)+1}, \">0\")", card_bg_red, num_int)
    ]

    for start_c, end_c, label, formula_val, bg_fill, n_fmt in kpi_defs:
        # Title Cell
        ws_dash.merge_cells(f"{start_c}5:{end_c}5")
        top_cell = ws_dash[f"{start_c}5"]
        top_cell.value = label
        top_cell.font = font_card_title
        top_cell.fill = bg_fill
        top_cell.alignment = align_center

        # Value Cell
        ws_dash.merge_cells(f"{start_c}6:{end_c}7")
        val_cell = ws_dash[f"{start_c}6"]
        val_cell.value = formula_val
        val_cell.font = font_card_val
        val_cell.fill = bg_fill
        val_cell.alignment = align_center
        val_cell.number_format = n_fmt

        for r in range(5, 8):
            for c_char in [start_c, end_c]:
                ws_dash[f"{c_char}{r}"].border = card_border

    # Section 1: Department Summary Table (Rows 10 to 18)
    ws_dash["B9"] = "DEPARTMENTAL PERFORMANCE BREAKDOWN"
    ws_dash["B9"].font = Font(name="Segoe UI", size=12, bold=True, color="1E293B")

    dept_headers = ["Department", "Invoices", "Invoiced Amount", "Collected Amount", "Outstanding AR", "Collection Rate"]
    for c_idx, h in enumerate(dept_headers, start=2):
        cell = ws_dash.cell(row=10, column=c_idx, value=h)
        format_cell(cell, font=font_header, fill=navy_header_fill, alignment=align_center)

    departments = sorted(df["Department"].unique())
    for r_idx, dept in enumerate(departments, start=11):
        ws_dash.cell(row=r_idx, column=2, value=dept).alignment = align_left
        ws_dash.cell(row=r_idx, column=3, value=f"=COUNTIF('Reconciled Master'!F$2:F${len(df)+1}, B{r_idx})").number_format = num_int
        ws_dash.cell(row=r_idx, column=4, value=f"=SUMIF('Reconciled Master'!F$2:F${len(df)+1}, B{r_idx}, 'Reconciled Master'!E$2:E${len(df)+1})").number_format = num_curr
        ws_dash.cell(row=r_idx, column=5, value=f"=SUMIF('Reconciled Master'!F$2:F${len(df)+1}, B{r_idx}, 'Reconciled Master'!G$2:G${len(df)+1})").number_format = num_curr
        ws_dash.cell(row=r_idx, column=6, value=f"=SUMIF('Reconciled Master'!F$2:F${len(df)+1}, B{r_idx}, 'Reconciled Master'!K$2:K${len(df)+1})").number_format = num_curr
        ws_dash.cell(row=r_idx, column=7, value=f"=E{r_idx}/D{r_idx}").number_format = num_pct

        fill = zebra_fill if r_idx % 2 == 0 else PatternFill(fill_type=None)
        for col_i in range(2, 8):
            c = ws_dash.cell(row=r_idx, column=col_i)
            c.font = font_regular
            c.border = thin_border
            if fill.fill_type: c.fill = fill
            if col_i in [3, 7]: c.alignment = align_center
            elif col_i in [4, 5, 6]: c.alignment = align_right

    # Department Total Row
    tot_row = 11 + len(departments)
    ws_dash.cell(row=tot_row, column=2, value="Total Portfolio").font = font_bold
    ws_dash.cell(row=tot_row, column=3, value=f"=SUM(C11:C{tot_row-1})").number_format = num_int
    ws_dash.cell(row=tot_row, column=4, value=f"=SUM(D11:D{tot_row-1})").number_format = num_curr
    ws_dash.cell(row=tot_row, column=5, value=f"=SUM(E11:E{tot_row-1})").number_format = num_curr
    ws_dash.cell(row=tot_row, column=6, value=f"=SUM(F11:F{tot_row-1})").number_format = num_curr
    ws_dash.cell(row=tot_row, column=7, value=f"=E{tot_row}/D{tot_row}").number_format = num_pct

    for col_i in range(2, 8):
        c = ws_dash.cell(row=tot_row, column=col_i)
        c.font = font_bold
        c.border = thick_bottom
        if col_i in [3, 7]: c.alignment = align_center
        elif col_i in [4, 5, 6]: c.alignment = align_right

    # Section 2: Aging Schedule (Rows 10 to 16 in col I to L)
    ws_dash["I9"] = "ACCOUNTS RECEIVABLE AGING"
    ws_dash["I9"].font = Font(name="Segoe UI", size=12, bold=True, color="1E293B")

    aging_headers = ["Aging Bucket", "Outstanding AR", "% Total AR", "Status"]
    for c_idx, h in enumerate(aging_headers, start=9):
        cell = ws_dash.cell(row=10, column=c_idx, value=h)
        format_cell(cell, font=font_header, fill=dark_blue_sub, alignment=align_center)

    aging_defs = [
        ("Current / Not Due", "=SUMIFS('Reconciled Master'!K$2:K$251, 'Reconciled Master'!P$2:P$251, \"Current / Not Due\")", "Performing"),
        ("1-30 Days", "=SUMIFS('Reconciled Master'!K$2:K$251, 'Reconciled Master'!P$2:P$251, \"1-30 Days\")", "Grace Period"),
        ("31-60 Days", "=SUMIFS('Reconciled Master'!K$2:K$251, 'Reconciled Master'!P$2:P$251, \"31-60 Days\")", "Follow-up Required"),
        ("61-90 Days", "=SUMIFS('Reconciled Master'!K$2:K$251, 'Reconciled Master'!P$2:P$251, \"61-90 Days\")", "High Risk"),
        ("90+ Days", "=SUMIFS('Reconciled Master'!K$2:K$251, 'Reconciled Master'!P$2:P$251, \"90+ Days\")", "Delinquent / Collection")
    ]

    for a_idx, (b_name, b_formula, b_status) in enumerate(aging_defs, start=11):
        ws_dash.cell(row=a_idx, column=9, value=b_name).alignment = align_left
        ws_dash.cell(row=a_idx, column=10, value=b_formula).number_format = num_curr
        ws_dash.cell(row=a_idx, column=11, value=f"=J{a_idx}/$F${tot_row}").number_format = num_pct
        ws_dash.cell(row=a_idx, column=12, value=b_status).alignment = align_center

        for col_i in range(9, 13):
            c = ws_dash.cell(row=a_idx, column=col_i)
            c.font = font_regular
            c.border = thin_border
            if col_i == 10: c.alignment = align_right
            elif col_i == 11: c.alignment = align_center

    # Total Aging Row
    tot_aging_row = 11 + len(aging_defs)
    ws_dash.cell(row=tot_aging_row, column=9, value="Total AR").font = font_bold
    ws_dash.cell(row=tot_aging_row, column=10, value=f"=SUM(J11:J{tot_aging_row-1})").number_format = num_curr
    ws_dash.cell(row=tot_aging_row, column=11, value=f"=SUM(K11:K{tot_aging_row-1})").number_format = num_pct
    ws_dash.cell(row=tot_aging_row, column=12, value="100%").alignment = align_center
    for col_i in range(9, 13):
        c = ws_dash.cell(row=tot_aging_row, column=col_i)
        c.font = font_bold
        c.border = thick_bottom
        if col_i == 10: c.alignment = align_right
        elif col_i in [11, 12]: c.alignment = align_center

    auto_fit_columns(ws_dash)

    # =========================================================================
    # SHEET 2: Reconciled Data Master
    # =========================================================================
    ws_master = wb.create_sheet(title="Reconciled Master")
    ws_master.views.sheetView[0].showGridLines = True

    master_headers = [
        "Invoice_ID", "Customer", "Invoice_Date", "Due_Date", "Invoice_Amount",
        "Department", "Total_Paid", "Payment_Count", "Latest_Payment_Date",
        "Payment_Methods", "Outstanding_Amount", "Collection_Rate_Pct",
        "Payment_Status", "Days_Overdue", "Late_Payment_Flag", "Aging_Bucket"
    ]

    for c_idx, h in enumerate(master_headers, start=1):
        cell = ws_master.cell(row=1, column=c_idx, value=h)
        format_cell(cell, font=font_header, fill=navy_header_fill, alignment=align_center)

    for r_idx, row in df.iterrows():
        r_num = r_idx + 2
        ws_master.cell(row=r_num, column=1, value=row["Invoice_ID"]).alignment = align_center
        ws_master.cell(row=r_num, column=2, value=row["Customer"]).alignment = align_left
        ws_master.cell(row=r_num, column=3, value=row["Invoice_Date"]).alignment = align_center
        ws_master.cell(row=r_num, column=4, value=row["Due_Date"]).alignment = align_center
        ws_master.cell(row=r_num, column=5, value=float(row["Invoice_Amount"])).number_format = num_curr
        ws_master.cell(row=r_num, column=6, value=row["Department"]).alignment = align_left
        ws_master.cell(row=r_num, column=7, value=float(row["Total_Paid"])).number_format = num_curr
        ws_master.cell(row=r_num, column=8, value=int(row["Payment_Count"])).alignment = align_center
        ws_master.cell(row=r_num, column=9, value=str(row["Latest_Payment_Date"]) if pd.notna(row["Latest_Payment_Date"]) else "").alignment = align_center
        ws_master.cell(row=r_num, column=10, value=str(row["Payment_Methods"])).alignment = align_left
        ws_master.cell(row=r_num, column=11, value=float(row["Outstanding_Amount"])).number_format = num_curr
        ws_master.cell(row=r_num, column=12, value=float(row["Collection_Rate_Pct"]) / 100.0).number_format = num_pct
        ws_master.cell(row=r_num, column=13, value=row["Payment_Status"]).alignment = align_center
        ws_master.cell(row=r_num, column=14, value=int(row["Days_Overdue"])).alignment = align_center
        ws_master.cell(row=r_num, column=15, value=row["Late_Payment_Flag"]).alignment = align_center
        ws_master.cell(row=r_num, column=16, value=row["Aging_Bucket"]).alignment = align_left

        for col_i in range(1, 17):
            c = ws_master.cell(row=r_num, column=col_i)
            c.font = font_regular
            c.border = thin_border

    # Master Total Row
    master_tot_row = len(df) + 2
    ws_master.cell(row=master_tot_row, column=1, value="Total").font = font_bold
    ws_master.cell(row=master_tot_row, column=5, value=f"=SUM(E2:E{master_tot_row-1})").number_format = num_curr
    ws_master.cell(row=master_tot_row, column=7, value=f"=SUM(G2:G{master_tot_row-1})").number_format = num_curr
    ws_master.cell(row=master_tot_row, column=11, value=f"=SUM(K2:K{master_tot_row-1})").number_format = num_curr
    ws_master.cell(row=master_tot_row, column=12, value=f"=G{master_tot_row}/E{master_tot_row}").number_format = num_pct

    for col_i in range(1, 17):
        c = ws_master.cell(row=master_tot_row, column=col_i)
        c.font = font_bold
        c.border = thick_bottom

    # Conditional Formatting on Reconciled Master
    # Red: overdue/unpaid, Yellow: partially paid, Green: paid
    green_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    green_font = Font(name="Segoe UI", size=10, color="065F46", bold=True)
    yellow_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    yellow_font = Font(name="Segoe UI", size=10, color="92400E", bold=True)
    red_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    red_font = Font(name="Segoe UI", size=10, color="991B1B", bold=True)

    status_range = f"M2:M{len(df)+1}"
    ws_master.conditional_formatting.add(
        status_range,
        CellIsRule(operator="equal", formula=['"Paid"'], stopIfTrue=True, fill=green_fill, font=green_font)
    )
    ws_master.conditional_formatting.add(
        status_range,
        CellIsRule(operator="equal", formula=['"Partially Paid"'], stopIfTrue=True, fill=yellow_fill, font=yellow_font)
    )
    ws_master.conditional_formatting.add(
        status_range,
        CellIsRule(operator="equal", formula=['"Unpaid"'], stopIfTrue=True, fill=red_fill, font=red_font)
    )

    # Highlight Days Overdue > 0 with Red
    overdue_range = f"N2:N{len(df)+1}"
    ws_master.conditional_formatting.add(
        overdue_range,
        CellIsRule(operator="greaterThan", formula=["0"], stopIfTrue=True, fill=red_fill, font=red_font)
    )

    ws_master.freeze_panes = "C2"
    auto_fit_columns(ws_master)

    # =========================================================================
    # SHEET 3: Pivot Table - Customer Outstanding
    # =========================================================================
    ws_piv_cust = wb.create_sheet(title="Pivot_Customer_Outstanding")
    ws_piv_cust.views.sheetView[0].showGridLines = True

    ws_piv_cust["B2"] = "PIVOT REPORT: OUTSTANDING BALANCES BY CUSTOMER"
    ws_piv_cust["B2"].font = font_title

    cust_piv_headers = [
        "Customer", "Total Invoices", "Invoiced Amount", "Collected Amount",
        "Outstanding Amount", "Collection Rate %", "Max Days Overdue"
    ]
    for c_idx, h in enumerate(cust_piv_headers, start=2):
        cell = ws_piv_cust.cell(row=4, column=c_idx, value=h)
        format_cell(cell, font=font_header, fill=navy_header_fill, alignment=align_center)

    # Summarize per customer sorted by Outstanding Amount descending
    cust_summary = (
        df.groupby("Customer")
        .agg(
            Invoices=("Invoice_ID", "count"),
            Invoiced=("Invoice_Amount", "sum"),
            Collected=("Total_Paid", "sum"),
            Outstanding=("Outstanding_Amount", "sum"),
            Max_Overdue=("Days_Overdue", "max")
        )
        .reset_index()
        .sort_values(by="Outstanding", ascending=False)
    )

    for r_idx, c_row in cust_summary.iterrows():
        row_pos = ws_piv_cust.max_row + 1
        ws_piv_cust.cell(row=row_pos, column=2, value=c_row["Customer"]).alignment = align_left
        ws_piv_cust.cell(row=row_pos, column=3, value=int(c_row["Invoices"])).alignment = align_center
        ws_piv_cust.cell(row=row_pos, column=4, value=float(c_row["Invoiced"])).number_format = num_curr
        ws_piv_cust.cell(row=row_pos, column=5, value=float(c_row["Collected"])).number_format = num_curr
        ws_piv_cust.cell(row=row_pos, column=6, value=float(c_row["Outstanding"])).number_format = num_curr
        ws_piv_cust.cell(row=row_pos, column=7, value=f"=E{row_pos}/D{row_pos}").number_format = num_pct
        ws_piv_cust.cell(row=row_pos, column=8, value=int(c_row["Max_Overdue"])).alignment = align_center

        fill = zebra_fill if row_pos % 2 == 0 else PatternFill(fill_type=None)
        for c_i in range(2, 9):
            c = ws_piv_cust.cell(row=row_pos, column=c_i)
            c.font = font_regular
            c.border = thin_border
            if fill.fill_type: c.fill = fill

    # Totals Row
    cust_tot_row = ws_piv_cust.max_row + 1
    ws_piv_cust.cell(row=cust_tot_row, column=2, value="Grand Total").font = font_bold
    ws_piv_cust.cell(row=cust_tot_row, column=3, value=f"=SUM(C5:C{cust_tot_row-1})").number_format = num_int
    ws_piv_cust.cell(row=cust_tot_row, column=4, value=f"=SUM(D5:D{cust_tot_row-1})").number_format = num_curr
    ws_piv_cust.cell(row=cust_tot_row, column=5, value=f"=SUM(E5:E{cust_tot_row-1})").number_format = num_curr
    ws_piv_cust.cell(row=cust_tot_row, column=6, value=f"=SUM(F5:F{cust_tot_row-1})").number_format = num_curr
    ws_piv_cust.cell(row=cust_tot_row, column=7, value=f"=E{cust_tot_row}/D{cust_tot_row}").number_format = num_pct
    ws_piv_cust.cell(row=cust_tot_row, column=8, value=f"=MAX(H5:H{cust_tot_row-1})").alignment = align_center

    for c_i in range(2, 9):
        c = ws_piv_cust.cell(row=cust_tot_row, column=c_i)
        c.font = font_bold
        c.border = thick_bottom

    # Highlight top outstanding > $300k
    ws_piv_cust.conditional_formatting.add(
        f"F5:F{cust_tot_row-1}",
        CellIsRule(operator="greaterThan", formula=["300000"], stopIfTrue=True, fill=red_fill, font=red_font)
    )

    auto_fit_columns(ws_piv_cust)

    # =========================================================================
    # SHEET 4: Pivot Table - Invoice Amount by Department
    # =========================================================================
    ws_piv_dept = wb.create_sheet(title="Pivot_Dept_Invoice_Amount")
    ws_piv_dept.views.sheetView[0].showGridLines = True

    ws_piv_dept["B2"] = "PIVOT REPORT: INVOICE & REVENUE DISTRIBUTION BY DEPARTMENT"
    ws_piv_dept["B2"].font = font_title

    dept_piv_headers = [
        "Department", "Total Invoices", "Invoice Amount", "% Share of Revenue",
        "Collected Amount", "Outstanding Amount", "Collection Rate %"
    ]
    for c_idx, h in enumerate(dept_piv_headers, start=2):
        cell = ws_piv_dept.cell(row=4, column=c_idx, value=h)
        format_cell(cell, font=font_header, fill=navy_header_fill, alignment=align_center)

    dept_summary = (
        df.groupby("Department")
        .agg(
            Invoices=("Invoice_ID", "count"),
            Invoiced=("Invoice_Amount", "sum"),
            Collected=("Total_Paid", "sum"),
            Outstanding=("Outstanding_Amount", "sum")
        )
        .reset_index()
        .sort_values(by="Invoiced", ascending=False)
    )

    for _, d_row in dept_summary.iterrows():
        row_pos = ws_piv_dept.max_row + 1
        ws_piv_dept.cell(row=row_pos, column=2, value=d_row["Department"]).alignment = align_left
        ws_piv_dept.cell(row=row_pos, column=3, value=int(d_row["Invoices"])).alignment = align_center
        ws_piv_dept.cell(row=row_pos, column=4, value=float(d_row["Invoiced"])).number_format = num_curr
        ws_piv_dept.cell(row=row_pos, column=5, value=f"=D{row_pos}/$D$11").number_format = num_pct
        ws_piv_dept.cell(row=row_pos, column=6, value=float(d_row["Collected"])).number_format = num_curr
        ws_piv_dept.cell(row=row_pos, column=7, value=float(d_row["Outstanding"])).number_format = num_curr
        ws_piv_dept.cell(row=row_pos, column=8, value=f"=F{row_pos}/D{row_pos}").number_format = num_pct

        fill = zebra_fill if row_pos % 2 == 0 else PatternFill(fill_type=None)
        for c_i in range(2, 9):
            c = ws_piv_dept.cell(row=row_pos, column=c_i)
            c.font = font_regular
            c.border = thin_border
            if fill.fill_type: c.fill = fill

    dept_tot_row = ws_piv_dept.max_row + 1
    ws_piv_dept.cell(row=dept_tot_row, column=2, value="Grand Total").font = font_bold
    ws_piv_dept.cell(row=dept_tot_row, column=3, value=f"=SUM(C5:C{dept_tot_row-1})").number_format = num_int
    ws_piv_dept.cell(row=dept_tot_row, column=4, value=f"=SUM(D5:D{dept_tot_row-1})").number_format = num_curr
    ws_piv_dept.cell(row=dept_tot_row, column=5, value="100.0%").alignment = align_center
    ws_piv_dept.cell(row=dept_tot_row, column=6, value=f"=SUM(F5:F{dept_tot_row-1})").number_format = num_curr
    ws_piv_dept.cell(row=dept_tot_row, column=7, value=f"=SUM(G5:G{dept_tot_row-1})").number_format = num_curr
    ws_piv_dept.cell(row=dept_tot_row, column=8, value=f"=F{dept_tot_row}/D{dept_tot_row}").number_format = num_pct

    for c_i in range(2, 9):
        c = ws_piv_dept.cell(row=dept_tot_row, column=c_i)
        c.font = font_bold
        c.border = thick_bottom

    auto_fit_columns(ws_piv_dept)

    # Save to all requested paths
    for out_p in OUTPUT_PATHS:
        os.makedirs(os.path.dirname(out_p) if os.path.dirname(out_p) else ".", exist_ok=True)
        wb.save(out_p)
        print(f">> Excel workbook saved successfully -> {out_p}")

if __name__ == "__main__":
    generate_excel_report()

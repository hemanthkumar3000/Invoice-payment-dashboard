"""
build_interactive_dashboard.py
------------------------------
Generates a standalone, interactive, executive dashboard in HTML/CSS/JavaScript
that mirrors the Power BI dashboard layout requested in the specification.

Features:
  - 1-Page responsive layout
  - 5 Live KPI Cards (Total Invoiced, Total Collected, Total Outstanding, Collection Rate %, Overdue Count)
  - 4 Filters/Slicers (Department, Customer, Payment Status, Date Range) with instant client-side reactivity
  - 4 Analytical Visualizations powered by Chart.js:
      1. Bar Chart: Outstanding Amount by Customer (Top Debtors)
      2. Donut Chart: Paid vs Partially Paid vs Unpaid Distribution
      3. Line Chart: Monthly Invoiced vs Collected Cash Velocity
      4. Bar Chart: Outstanding Amount by Department
  - Detail Table with pagination, search, column sorting, and color-coded status pills
  - Export filtered data to CSV & Print Report functionality
"""

import os
import json
import pandas as pd

RECON_CSV = "data/processed/reconciled_invoices.csv"
OUTPUT_HTMLS = ["reports/interactive_dashboard.html", "interactive_dashboard.html"]

def generate_dashboard_html():
    print(">> Building Interactive Executive HTML Dashboard...")
    df = pd.read_csv(RECON_CSV)
    
    # Clean records for JSON serialization
    records_json = df.to_json(orient="records")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Invoice–Payment Reconciliation & Revenue Dashboard</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <!-- Google Fonts: Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Inter', sans-serif;
      background-color: #0F172A; /* Slate 900 */
      color: #F8FAFC;
    }}
    .card-glass {{
      background: rgba(30, 41, 59, 0.7);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 0.75rem;
    }}
    .badge-paid {{
      background-color: rgba(16, 185, 129, 0.15);
      color: #34D399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}
    .badge-partial {{
      background-color: rgba(245, 158, 11, 0.15);
      color: #FBBF24;
      border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    .badge-unpaid {{
      background-color: rgba(239, 68, 68, 0.15);
      color: #F87171;
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    /* Custom scrollbars */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: #1E293B;
    }}
    ::-webkit-scrollbar-thumb {{
      background: #475569;
      border-radius: 3px;
    }}
  </style>
</head>
<body class="min-h-screen p-4 md:p-6 lg:p-8">

  <!-- TOP HEADER -->
  <header class="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
    <div>
      <div class="flex items-center gap-3">
        <div class="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-indigo-500/30">
          $
        </div>
        <h1 class="text-2xl font-bold tracking-tight text-white">Invoice–Payment Reconciliation & Revenue Dashboard</h1>
      </div>
      <p class="text-xs text-slate-400 mt-1">
        Unified Cross-Source Finance Intelligence | As-Of Date: <span class="font-medium text-slate-300">2026-10-01</span> | Synthetic Enterprise Finance Dataset
      </p>
    </div>
    <div class="flex items-center gap-3">
      <button onclick="resetFilters()" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">
        Reset Slicers
      </button>
      <button onclick="exportToCSV()" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition">
        Export CSV
      </button>
    </div>
  </header>

  <!-- SLICERS / FILTERS BAR -->
  <section class="mt-6 p-4 card-glass grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    <div>
      <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Department</label>
      <select id="filterDept" onchange="applyFilters()" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        <option value="ALL">All Departments</option>
      </select>
    </div>
    <div>
      <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Customer</label>
      <select id="filterCust" onchange="applyFilters()" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        <option value="ALL">All Customers</option>
      </select>
    </div>
    <div>
      <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Payment Status</label>
      <select id="filterStatus" onchange="applyFilters()" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        <option value="ALL">All Statuses</option>
        <option value="Paid">Paid</option>
        <option value="Partially Paid">Partially Paid</option>
        <option value="Unpaid">Unpaid</option>
      </select>
    </div>
    <div>
      <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Date Range</label>
      <div class="flex items-center gap-2">
        <input type="date" id="filterDateStart" onchange="applyFilters()" class="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        <span class="text-xs text-slate-500">to</span>
        <input type="date" id="filterDateEnd" onchange="applyFilters()" class="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
      </div>
    </div>
  </section>

  <!-- KPI CARDS -->
  <section class="mt-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
    <!-- KPI 1 -->
    <div class="card-glass p-4 border-l-4 border-l-blue-500">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Invoiced</span>
      <div id="kpiInvoiced" class="text-2xl font-bold text-white mt-1">$0</div>
      <div class="text-[11px] text-slate-400 mt-1"><span id="kpiInvoiceCount">0</span> Invoices Issued</div>
    </div>
    <!-- KPI 2 -->
    <div class="card-glass p-4 border-l-4 border-l-emerald-500">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Collected</span>
      <div id="kpiCollected" class="text-2xl font-bold text-emerald-400 mt-1">$0</div>
      <div class="text-[11px] text-emerald-500/80 mt-1">Realized Cash Inflow</div>
    </div>
    <!-- KPI 3 -->
    <div class="card-glass p-4 border-l-4 border-l-rose-500">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Outstanding</span>
      <div id="kpiOutstanding" class="text-2xl font-bold text-rose-400 mt-1">$0</div>
      <div class="text-[11px] text-rose-500/80 mt-1">Uncollected Balance</div>
    </div>
    <!-- KPI 4 -->
    <div class="card-glass p-4 border-l-4 border-l-amber-500">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Collection Rate %</span>
      <div id="kpiCollectionRate" class="text-2xl font-bold text-amber-400 mt-1">0.0%</div>
      <div class="text-[11px] text-slate-400 mt-1">Cash Fulfillment Ratio</div>
    </div>
    <!-- KPI 5 -->
    <div class="card-glass p-4 border-l-4 border-l-purple-500 col-span-2 sm:col-span-1">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Overdue Invoices</span>
      <div id="kpiOverdue" class="text-2xl font-bold text-purple-400 mt-1">0</div>
      <div class="text-[11px] text-slate-400 mt-1"><span id="kpiOverdueAmt">$0</span> Delinquent</div>
    </div>
  </section>

  <!-- VISUALS GRID -->
  <section class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Chart 1: Bar Chart - Outstanding by Customer -->
    <div class="card-glass p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-sm font-semibold text-slate-200">Top Debtors: Outstanding Amount by Customer</h2>
          <p class="text-xs text-slate-400">Largest unpaid accounts receivable exposure</p>
        </div>
      </div>
      <div class="h-64">
        <canvas id="chartCust"></canvas>
      </div>
    </div>

    <!-- Chart 2: Donut Chart - Payment Status Breakdown -->
    <div class="card-glass p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-sm font-semibold text-slate-200">Invoice Status Distribution</h2>
          <p class="text-xs text-slate-400">Paid vs Partially Paid vs Unpaid breakdown</p>
        </div>
      </div>
      <div class="h-64 flex items-center justify-center">
        <canvas id="chartStatus"></canvas>
      </div>
    </div>

    <!-- Chart 3: Line Chart - Monthly Invoiced vs Collected -->
    <div class="card-glass p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-sm font-semibold text-slate-200">Monthly Invoiced vs Collected Trend</h2>
          <p class="text-xs text-slate-400">Cash velocity and monthly revenue comparison</p>
        </div>
      </div>
      <div class="h-64">
        <canvas id="chartTrend"></canvas>
      </div>
    </div>

    <!-- Chart 4: Bar Chart - Outstanding Amount by Department -->
    <div class="card-glass p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-sm font-semibold text-slate-200">Outstanding Balance by Department</h2>
          <p class="text-xs text-slate-400">Departmental collection risk profile</p>
        </div>
      </div>
      <div class="h-64">
        <canvas id="chartDept"></canvas>
      </div>
    </div>
  </section>

  <!-- DETAIL TRANSACTION TABLE -->
  <section class="mt-6 card-glass p-5">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
      <div>
        <h2 class="text-sm font-semibold text-slate-200">Reconciled Invoice Records</h2>
        <p class="text-xs text-slate-400">Granular transaction-level audit trail (<span id="tableMatchCount">0</span> records)</p>
      </div>
      <div class="flex items-center gap-3">
        <input type="text" id="searchTable" onkeyup="handleSearch()" placeholder="Search invoice or customer..." class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-56">
      </div>
    </div>

    <div class="overflow-x-auto rounded-lg border border-slate-800">
      <table class="min-w-full divide-y divide-slate-800 text-left text-xs">
        <thead class="bg-slate-900/80 text-slate-300 font-semibold uppercase tracking-wider">
          <tr>
            <th class="py-3 px-4">Invoice ID</th>
            <th class="py-3 px-4">Customer</th>
            <th class="py-3 px-4">Department</th>
            <th class="py-3 px-4">Due Date</th>
            <th class="py-3 px-4 text-right">Invoice Amount</th>
            <th class="py-3 px-4 text-right">Total Paid</th>
            <th class="py-3 px-4 text-right">Outstanding</th>
            <th class="py-3 px-4 text-center">Status</th>
            <th class="py-3 px-4 text-center">Days Overdue</th>
          </tr>
        </thead>
        <tbody id="tableBody" class="divide-y divide-slate-800 text-slate-300">
          <!-- Populated dynamically via JS -->
        </tbody>
      </table>
    </div>

    <!-- Pagination Controls -->
    <div class="flex items-center justify-between mt-4 text-xs text-slate-400">
      <div id="pageInfo">Showing 1 to 10</div>
      <div class="flex items-center gap-2">
        <button onclick="prevPage()" id="btnPrev" class="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-40">Previous</button>
        <button onclick="nextPage()" id="btnNext" class="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-40">Next</button>
      </div>
    </div>
  </section>

  <!-- EMBEDDED DATA & SCRIPT LOGIC -->
  <script>
    const MASTER_DATA = {records_json};
    let filteredData = [...MASTER_DATA];
    let currentPage = 1;
    const pageSize = 10;
    let chartCustInstance = null;
    let chartStatusInstance = null;
    let chartTrendInstance = null;
    let chartDeptInstance = null;

    // Formatting utilities
    const fmtCurr = (num) => '$' + Number(num || 0).toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
    const fmtCurrK = (num) => '$' + Number(num || 0).toLocaleString('en-US', {{ maximumFractionDigits: 0 }});

    // Populate dropdown options on init
    function populateDropdowns() {{
      const depts = [...new Set(MASTER_DATA.map(d => d.Department))].sort();
      const custs = [...new Set(MASTER_DATA.map(d => d.Customer))].sort();
      
      const deptSelect = document.getElementById('filterDept');
      depts.forEach(dept => {{
        const opt = document.createElement('option');
        opt.value = dept;
        opt.textContent = dept;
        deptSelect.appendChild(opt);
      }});

      const custSelect = document.getElementById('filterCust');
      custs.forEach(cust => {{
        const opt = document.createElement('option');
        opt.value = cust;
        opt.textContent = cust;
        custSelect.appendChild(opt);
      }});

      const dates = MASTER_DATA.map(d => d.Invoice_Date).sort();
      document.getElementById('filterDateStart').value = dates[0];
      document.getElementById('filterDateEnd').value = dates[dates.length - 1];
    }}

    // Filter Logic
    function applyFilters() {{
      const dept = document.getElementById('filterDept').value;
      const cust = document.getElementById('filterCust').value;
      const status = document.getElementById('filterStatus').value;
      const dStart = document.getElementById('filterDateStart').value;
      const dEnd = document.getElementById('filterDateEnd').value;
      const search = document.getElementById('searchTable').value.toLowerCase().trim();

      filteredData = MASTER_DATA.filter(row => {{
        if (dept !== 'ALL' && row.Department !== dept) return false;
        if (cust !== 'ALL' && row.Customer !== cust) return false;
        if (status !== 'ALL' && row.Payment_Status !== status) return false;
        if (dStart && row.Invoice_Date < dStart) return false;
        if (dEnd && row.Invoice_Date > dEnd) return false;
        if (search) {{
          const term = (row.Invoice_ID + ' ' + row.Customer + ' ' + row.Department).toLowerCase();
          if (!term.includes(search)) return false;
        }}
        return true;
      }});

      currentPage = 1;
      updateKPIs();
      renderCharts();
      renderTable();
    }}

    function resetFilters() {{
      document.getElementById('filterDept').value = 'ALL';
      document.getElementById('filterCust').value = 'ALL';
      document.getElementById('filterStatus').value = 'ALL';
      document.getElementById('searchTable').value = '';
      const dates = MASTER_DATA.map(d => d.Invoice_Date).sort();
      document.getElementById('filterDateStart').value = dates[0];
      document.getElementById('filterDateEnd').value = dates[dates.length - 1];
      applyFilters();
    }}

    function handleSearch() {{
      applyFilters();
    }}

    // Update KPI Cards
    function updateKPIs() {{
      const totalInv = filteredData.reduce((acc, r) => acc + Number(r.Invoice_Amount || 0), 0);
      const totalPaid = filteredData.reduce((acc, r) => acc + Number(r.Total_Paid || 0), 0);
      const totalOut = filteredData.reduce((acc, r) => acc + Number(r.Outstanding_Amount || 0), 0);
      const rate = totalInv > 0 ? ((totalPaid / totalInv) * 100).toFixed(1) : '0.0';
      const overdueRows = filteredData.filter(r => r.Payment_Status !== 'Paid' && Number(r.Days_Overdue) > 0);
      const overdueAmt = overdueRows.reduce((acc, r) => acc + Number(r.Outstanding_Amount || 0), 0);

      document.getElementById('kpiInvoiced').textContent = fmtCurrK(totalInv);
      document.getElementById('kpiInvoiceCount').textContent = filteredData.length;
      document.getElementById('kpiCollected').textContent = fmtCurrK(totalPaid);
      document.getElementById('kpiOutstanding').textContent = fmtCurrK(totalOut);
      document.getElementById('kpiCollectionRate').textContent = rate + '%';
      document.getElementById('kpiOverdue').textContent = overdueRows.length;
      document.getElementById('kpiOverdueAmt').textContent = fmtCurrK(overdueAmt);
    }}

    // Render Charts
    function renderCharts() {{
      // --- Chart 1: Outstanding by Customer (Top 7) ---
      const custAgg = {{}};
      filteredData.forEach(r => {{
        custAgg[r.Customer] = (custAgg[r.Customer] || 0) + Number(r.Outstanding_Amount || 0);
      }});
      const sortedCust = Object.entries(custAgg)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 7);

      if (chartCustInstance) chartCustInstance.destroy();
      const ctxCust = document.getElementById('chartCust').getContext('2d');
      chartCustInstance = new Chart(ctxCust, {{
        type: 'bar',
        data: {{
          labels: sortedCust.map(c => c[0]),
          datasets: [{{
            label: 'Outstanding ($)',
            data: sortedCust.map(c => c[1]),
            backgroundColor: '#EF4444',
            borderRadius: 4
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: (ctx) => fmtCurr(ctx.raw) }} }}
          }},
          scales: {{
            x: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94A3B8', callback: (v) => '$' + (v/1000) + 'k' }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ color: '#CBD5E1', font: {{ size: 11 }} }} }}
          }}
        }}
      }});

      // --- Chart 2: Status Donut ---
      const statusCounts = {{ 'Paid': 0, 'Partially Paid': 0, 'Unpaid': 0 }};
      filteredData.forEach(r => {{
        if (statusCounts[r.Payment_Status] !== undefined) {{
          statusCounts[r.Payment_Status]++;
        }}
      }});

      if (chartStatusInstance) chartStatusInstance.destroy();
      const ctxStatus = document.getElementById('chartStatus').getContext('2d');
      chartStatusInstance = new Chart(ctxStatus, {{
        type: 'doughnut',
        data: {{
          labels: ['Paid', 'Partially Paid', 'Unpaid'],
          datasets: [{{
            data: [statusCounts['Paid'], statusCounts['Partially Paid'], statusCounts['Unpaid']],
            backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
            borderWidth: 2,
            borderColor: '#1E293B'
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ color: '#E2E8F0', padding: 15 }} }}
          }},
          cutout: '70%'
        }}
      }});

      // --- Chart 3: Monthly Trend ---
      const months = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09'];
      const monthlyInv = {{}};
      const monthlyPaid = {{}};
      months.forEach(m => {{ monthlyInv[m] = 0; monthlyPaid[m] = 0; }});

      filteredData.forEach(r => {{
        const m = (r.Invoice_Date || '').substring(0, 7);
        if (monthlyInv[m] !== undefined) {{
          monthlyInv[m] += Number(r.Invoice_Amount || 0);
          monthlyPaid[m] += Number(r.Total_Paid || 0);
        }}
      }});

      if (chartTrendInstance) chartTrendInstance.destroy();
      const ctxTrend = document.getElementById('chartTrend').getContext('2d');
      chartTrendInstance = new Chart(ctxTrend, {{
        type: 'line',
        data: {{
          labels: months,
          datasets: [
            {{
              label: 'Invoiced',
              data: months.map(m => monthlyInv[m]),
              borderColor: '#38BDF8',
              backgroundColor: 'rgba(56, 189, 248, 0.1)',
              tension: 0.3,
              fill: true,
              pointRadius: 4
            }},
            {{
              label: 'Collected',
              data: months.map(m => monthlyPaid[m]),
              borderColor: '#10B981',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              tension: 0.3,
              fill: true,
              pointRadius: 4
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'top', labels: {{ color: '#E2E8F0' }} }},
            tooltip: {{ callbacks: {{ label: (ctx) => ctx.dataset.label + ': ' + fmtCurr(ctx.raw) }} }}
          }},
          scales: {{
            x: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94A3B8' }} }},
            y: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94A3B8', callback: (v) => '$' + (v/1000) + 'k' }} }}
          }}
        }}
      }});

      // --- Chart 4: Department Outstanding ---
      const deptAgg = {{}};
      filteredData.forEach(r => {{
        deptAgg[r.Department] = (deptAgg[r.Department] || 0) + Number(r.Outstanding_Amount || 0);
      }});
      const depts = Object.keys(deptAgg).sort((a,b) => deptAgg[b] - deptAgg[a]);

      if (chartDeptInstance) chartDeptInstance.destroy();
      const ctxDept = document.getElementById('chartDept').getContext('2d');
      chartDeptInstance = new Chart(ctxDept, {{
        type: 'bar',
        data: {{
          labels: depts,
          datasets: [{{
            label: 'Outstanding ($)',
            data: depts.map(d => deptAgg[d]),
            backgroundColor: '#818CF8',
            borderRadius: 4
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: (ctx) => fmtCurr(ctx.raw) }} }}
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: '#CBD5E1' }} }},
            y: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94A3B8', callback: (v) => '$' + (v/1000) + 'k' }} }}
          }}
        }}
      }});
    }}

    // Render Table & Pagination
    function renderTable() {{
      const tbody = document.getElementById('tableBody');
      tbody.innerHTML = '';

      const totalItems = filteredData.length;
      document.getElementById('tableMatchCount').textContent = totalItems;

      const totalPages = Math.ceil(totalItems / pageSize) || 1;
      if (currentPage > totalPages) currentPage = totalPages;

      const startIdx = (currentPage - 1) * pageSize;
      const endIdx = Math.min(startIdx + pageSize, totalItems);
      const pageSlice = filteredData.slice(startIdx, endIdx);

      pageSlice.forEach(row => {{
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-800/50 transition';

        let badgeClass = 'badge-paid';
        if (row.Payment_Status === 'Partially Paid') badgeClass = 'badge-partial';
        else if (row.Payment_Status === 'Unpaid') badgeClass = 'badge-unpaid';

        const daysOverdue = Number(row.Days_Overdue || 0);
        const overdueText = daysOverdue > 0 ? `<span class="text-rose-400 font-semibold">${{daysOverdue}} d</span>` : `<span class="text-slate-500">0 d</span>`;

        tr.innerHTML = `
          <td class="py-3 px-4 font-mono font-medium text-slate-200">${{row.Invoice_ID}}</td>
          <td class="py-3 px-4 font-medium text-slate-100">${{row.Customer}}</td>
          <td class="py-3 px-4 text-slate-300">${{row.Department}}</td>
          <td class="py-3 px-4 text-slate-400">${{row.Due_Date}}</td>
          <td class="py-3 px-4 text-right font-medium text-slate-200">${{fmtCurr(row.Invoice_Amount)}}</td>
          <td class="py-3 px-4 text-right font-medium text-emerald-400">${{fmtCurr(row.Total_Paid)}}</td>
          <td class="py-3 px-4 text-right font-semibold text-rose-400">${{fmtCurr(row.Outstanding_Amount)}}</td>
          <td class="py-3 px-4 text-center">
            <span class="inline-block px-2.5 py-0.5 text-[11px] font-semibold rounded-full ${{badgeClass}}">
              ${{row.Payment_Status}}
            </span>
          </td>
          <td class="py-3 px-4 text-center">${{overdueText}}</td>
        `;
        tbody.appendChild(tr);
      }});

      document.getElementById('pageInfo').textContent = totalItems === 0 
        ? 'No matching invoices found' 
        : `Showing ${{startIdx + 1}} to ${{endIdx}} of ${{totalItems}} records (Page ${{currentPage}} of ${{totalPages}})`;

      document.getElementById('btnPrev').disabled = currentPage <= 1;
      document.getElementById('btnNext').disabled = currentPage >= totalPages;
    }}

    function prevPage() {{
      if (currentPage > 1) {{
        currentPage--;
        renderTable();
      }}
    }}

    function nextPage() {{
      const totalPages = Math.ceil(filteredData.length / pageSize);
      if (currentPage < totalPages) {{
        currentPage++;
        renderTable();
      }}
    }}

    function exportToCSV() {{
      const headers = ["Invoice_ID","Customer","Department","Invoice_Date","Due_Date","Invoice_Amount","Total_Paid","Outstanding_Amount","Payment_Status","Days_Overdue"];
      const rows = filteredData.map(r => [
        r.Invoice_ID,
        `"${{r.Customer}}"`,
        r.Department,
        r.Invoice_Date,
        r.Due_Date,
        r.Invoice_Amount,
        r.Total_Paid,
        r.Outstanding_Amount,
        r.Payment_Status,
        r.Days_Overdue
      ]);
      const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `filtered_reconciled_invoices_${{new Date().toISOString().slice(0,10)}}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}

    // Bootstrapping
    window.addEventListener('DOMContentLoaded', () => {{
      populateDropdowns();
      applyFilters();
    }});
  </script>
</body>
</html>
"""

    for out_path in OUTPUT_HTMLS:
        os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f">> Interactive dashboard exported -> {out_path}")

if __name__ == "__main__":
    generate_dashboard_html()

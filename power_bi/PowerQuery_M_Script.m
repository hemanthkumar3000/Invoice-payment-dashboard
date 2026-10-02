/*
========================================================================================
POWER QUERY (M) SCRIPT: INVOICE-PAYMENT RECONCILIATION
Instructions:
  1. In Power BI Desktop, click "Home" -> "Transform data" -> Open Power Query Editor.
  2. Click "Home" -> "Advanced Editor".
  3. Replace the file paths with your local invoices.csv and payments.csv paths.
========================================================================================
*/

let
    // 1. Ingest Invoices
    Source_Invoices = Csv.Document(File.Contents("C:\Users\kotah\OneDrive\Documents\Desktop\Invoice-payment-dashboard\data\raw\invoices.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Promote_Inv_Headers = Table.PromoteHeaders(Source_Invoices, [PromoteAllScalars=true]),
    Dedupe_Invoices = Table.Distinct(Promote_Inv_Headers, {"Invoice_ID"}),
    Transform_Inv_Types = Table.TransformColumnTypes(Dedupe_Invoices, {
        {"Invoice_ID", type text},
        {"Customer", type text},
        {"Invoice_Date", type date},
        {"Due_Date", type date},
        {"Invoice_Amount", type number},
        {"Department", type text}
    }),
    Trim_Inv_Customer = Table.TransformColumns(Transform_Inv_Types, {{"Customer", Text.Trim, type text}}),

    // 2. Ingest Payments
    Source_Payments = Csv.Document(File.Contents("C:\Users\kotah\OneDrive\Documents\Desktop\Invoice-payment-dashboard\data\raw\payments.csv"), [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Promote_Pay_Headers = Table.PromoteHeaders(Source_Payments, [PromoteAllScalars=true]),
    Dedupe_Payments = Table.Distinct(Promote_Pay_Headers, {"Payment_ID"}),
    Clean_Pay_Amounts = Table.ReplaceValue(Dedupe_Payments, "", "0", Replacer.ReplaceValue, {"Payment_Amount"}),
    Transform_Pay_Types = Table.TransformColumnTypes(Clean_Pay_Amounts, {
        {"Payment_ID", type text},
        {"Invoice_ID", type text},
        {"Payment_Date", type date},
        {"Payment_Amount", type number},
        {"Payment_Method", type text}
    }),

    // 3. Aggregate Payments by Invoice_ID
    Grouped_Payments = Table.Group(Transform_Pay_Types, {"Invoice_ID"}, {
        {"Total_Paid", each List.Sum([Payment_Amount]), type nullable number},
        {"Payment_Count", each Table.RowCount(_), Int64.Type},
        {"Latest_Payment_Date", each List.Max([Payment_Date]), type nullable date}
    }),

    // 4. Merge Invoices with Payments (Left Outer Join)
    Merge_Invoices_Payments = Table.NestedJoin(Trim_Inv_Customer, {"Invoice_ID"}, Grouped_Payments, {"Invoice_ID"}, "PaymentGroup", JoinKind.LeftOuter),
    Expand_Payments = Table.ExpandTableColumn(Merge_Invoices_Payments, "PaymentGroup", {"Total_Paid", "Payment_Count", "Latest_Payment_Date"}, {"Total_Paid", "Payment_Count", "Latest_Payment_Date"}),

    // 5. Replace Nulls & Derive Calculated Fields
    Fill_Null_Paid = Table.ReplaceValue(Expand_Payments, null, 0, Replacer.ReplaceValue, {"Total_Paid"}),
    Fill_Null_Count = Table.ReplaceValue(Fill_Null_Paid, null, 0, Replacer.ReplaceValue, {"Payment_Count"}),

    // Outstanding_Amount = Invoice_Amount - Total_Paid
    Add_Outstanding = Table.AddColumn(Fill_Null_Count, "Outstanding_Amount", each Number.Max({0, [Invoice_Amount] - [Total_Paid]}), type number),

    // Payment_Status = Paid / Partially Paid / Unpaid
    Add_Status = Table.AddColumn(Add_Outstanding, "Payment_Status", each 
        if [Total_Paid] >= [Invoice_Amount] then "Paid"
        else if [Total_Paid] > 0 then "Partially Paid"
        else "Unpaid", 
        type text
    ),

    // Reference Date for Aging: 2026-10-01
    RefDate = #date(2026, 10, 1),

    // Days_Overdue
    Add_Days_Overdue = Table.AddColumn(Add_Status, "Days_Overdue", each 
        if [Payment_Status] = "Paid" then 0
        else if RefDate > [Due_Date] then Duration.Days(RefDate - [Due_Date])
        else 0, 
        Int64.Type
    ),

    // Late_Payment_Flag
    Add_Late_Flag = Table.AddColumn(Add_Days_Overdue, "Late_Payment_Flag", each 
        if [Payment_Status] = "Paid" then (if [Latest_Payment_Date] <> null and [Latest_Payment_Date] > [Due_Date] then "Yes" else "No")
        else if [Days_Overdue] > 0 then "Yes"
        else "No", 
        type text
    ),

    // Aging_Bucket
    Add_Aging_Bucket = Table.AddColumn(Add_Late_Flag, "Aging_Bucket", each 
        if [Payment_Status] = "Paid" then "Settled / Not Due"
        else if [Days_Overdue] = 0 then "Current / Not Due"
        else if [Days_Overdue] <= 30 then "1-30 Days"
        else if [Days_Overdue] <= 60 then "31-60 Days"
        else if [Days_Overdue] <= 90 then "61-90 Days"
        else "90+ Days", 
        type text
    ),

    // Final Type Enforcements
    Final_Types = Table.TransformColumnTypes(Add_Aging_Bucket, {
        {"Outstanding_Amount", type number},
        {"Payment_Status", type text},
        {"Days_Overdue", Int64.Type},
        {"Late_Payment_Flag", type text},
        {"Aging_Bucket", type text}
    })
in
    Final_Types

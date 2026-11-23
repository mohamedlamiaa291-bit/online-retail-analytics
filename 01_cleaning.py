"""Chapter 1 - Data Cleaning | Online Retail II (Dec 2009 - Dec 2011)

Input : data/online_retail_cleaned.csv
Output: sales_clean.csv      -> completed orders, real products only (sales / product / geo analysis)
        customers_clean.csv  -> sales_clean rows that have a Customer ID (RFM / cohort)
        cancelled.csv        -> cancelled lines (cancellation analysis)
        cleaning_summary.csv -> before/after numbers for the portfolio
"""
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
SRC = ROOT / "data" / "online_retail_cleaned.csv"   # put the input file in data/

df = pd.read_csv(SRC, parse_dates=["InvoiceDate"], dtype={"Invoice": str, "StockCode": str})
steps = [("Raw file", len(df), df.TotalAmount.sum())]

# 1) Split cancelled vs completed
cancelled = df[df.Status == "Cancelled"].copy()
sales = df[df.Status == "Completed"].copy()
steps.append(("Completed only", len(sales), sales.TotalAmount.sum()))

# 2) Drop non-product codes (gift vouchers, DCGS* items)
is_product = sales.StockCode.str.match(r"^\d{5}")
removed_nonprod = sales[~is_product]
sales = sales[is_product].copy()
steps.append(("Real products only", len(sales), sales.TotalAmount.sum()))

# 3) Flag extreme lines (do not drop - lets us show analysis with/without)
sales["IsOutlier"] = (sales.TotalAmount > 5000) | (sales.Quantity > 5000)

# 4) Customer ID as integer-like string, flag missing
sales["HasCustomer"] = sales["Customer ID"].notna()
sales["Customer ID"] = sales["Customer ID"].astype("Int64")

# 5) Mark the incomplete last month (data ends 9 Dec 2011)
sales["IsPartialMonth"] = sales.YearMonth == "2011-12"

customers = sales[sales.HasCustomer].copy()
steps.append(("With Customer ID (RFM/Cohort)", len(customers), customers.TotalAmount.sum()))

sales.to_csv(f"{OUT}/sales_clean.csv", index=False)
customers.to_csv(f"{OUT}/customers_clean.csv", index=False)
cancelled.to_csv(f"{OUT}/cancelled.csv", index=False)

summary = pd.DataFrame(steps, columns=["Step", "Rows", "Revenue_GBP"]).round(0)
summary.to_csv(f"{OUT}/cleaning_summary.csv", index=False)

print(summary.to_string(index=False))
print("\nOutlier lines flagged:", int(sales.IsOutlier.sum()), "| revenue:", round(sales[sales.IsOutlier].TotalAmount.sum()))
print("Non-product rows removed:", len(removed_nonprod))
print("Cancellation rate (invoices):", round(cancelled.Invoice.nunique() / (cancelled.Invoice.nunique() + sales.Invoice.nunique()) * 100, 1), "%")
print("Cancelled value:", round(cancelled.TotalAmount.sum()))

# chase.py
import pandas as pd
import datetime
import re
import os

# Path to Chase CSV and date column
CSV_PATH = "./Credit Card Data/Imports/CHASE.csv"
DATE_COL = "Date"

# Patterns to ignore autopay or automatic payments
IGNORE_RE = re.compile(r"AUTOPAY|AUTOMATIC\s+PAYMENT", re.IGNORECASE)


def load_and_prep():
    # Read CSV
    df = pd.read_csv(CSV_PATH)
    # Rename the date column
    df.rename(columns={DATE_COL: "Transaction Date"}, inplace=True)
    # Filter out autopay transactions
    df = df[~df["Description"].str.contains(IGNORE_RE, na=False)]
    # Parse dates
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    # Keep only charges (negative amounts) and convert to positive
    df = df[df["Amount"] < 0]
    df["Amount"] = df["Amount"].abs()
    # Limit to current calendar year
    current_year = datetime.date.today().year
    df = df[df["Transaction Date"].dt.year == current_year]
    return df


def spend_by_month(df):
    # Group transactions by month
    df["Month"] = df["Transaction Date"].dt.to_period("M")
    monthly_spend = df.groupby("Month")["Amount"].sum()
    # Print monthly spend
    print("Chase CSP Monthly Spend YTD by Month")
    print(monthly_spend.to_frame(name="Month Spend"))
    # Print year-to-date total
    total_ytd = monthly_spend.sum()
    print(f"\nYear-to-Date Spend: ${total_ytd:.2f}")


if __name__ == "__main__":
    df = load_and_prep()
    spend_by_month(df)

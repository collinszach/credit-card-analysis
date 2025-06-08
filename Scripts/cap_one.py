# cap_one.py
import pandas as pd
import datetime
import re
import os

# Path to Capital One CSV and transaction date column
CSV_PATH = "./Credit Card Data/Imports/CAP_ONE.csv"

# Patterns to ignore autopay or automatic payments
IGNORE_RE = re.compile(r"AUTOPAY|AUTOMATIC\s+PAYMENT", re.IGNORECASE)


def load_and_prep():
    # Read CSV
    df = pd.read_csv(CSV_PATH)
    # Rename Debit to Amount and combine Credit if present
    df.rename(columns={"Debit": "Amount"}, inplace=True)
    if "Credit" in df.columns:
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce").fillna(0)
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0) - df["Credit"]
        df.drop(columns=["Credit"], inplace=True)
    # Filter out autopay transactions
    df = df[~df["Description"].str.contains(IGNORE_RE, na=False)]
    # Parse dates
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
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
    print("Venture X Monthly Spend YTD by Month")
    print(monthly_spend.to_frame(name="Month Spend"))
    # Print year-to-date total
    total_ytd = monthly_spend.sum()
    print(f"\nYear-to-Date Spend: ${total_ytd:.2f}")


if __name__ == "__main__":
    df = load_and_prep()
    spend_by_month(df)

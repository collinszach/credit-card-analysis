import subprocess
import sys
import os
import pandas as pd
import datetime
import re

# Path to the directory containing your card scripts and data
SCRIPTS_DIR = os.path.dirname(__file__)
IMPORT_DIR= "./Credit Card Data/Imports"
EXPORT_DIR = "./Credit Card Data/All-time Data"

# Utility to run each card-specific script
def run_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    print(f"\n=== Running {script_name} ===")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error in {script_name}:\n{result.stderr}")

# Filter out autopay/automatic payments
IGNORE_REGEX = re.compile(r"AUTOPAY|AUTOMATIC\s+PAYMENT", re.IGNORECASE)

def filter_autopay(df: pd.DataFrame) -> pd.DataFrame:
    if "Description" in df.columns:
        return df[~df["Description"].str.contains(IGNORE_REGEX, na=False)]
    return df

# Helper to load and prepare a single card's CSV for combination
def load_card(path: str, rename_cols: dict, card_name: str, has_credit: bool=False) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.rename(columns=rename_cols, inplace=True)
    if has_credit and "Credit" in df.columns:
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce").fillna(0)
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0) - df["Credit"]
        df.drop(columns=["Credit"], inplace=True)
    df = filter_autopay(df)
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    # Special handling for Chase: invert the sign of every Amount
    if card_name == "Chase Sapphire Preferred":
        df["Amount"] = -df["Amount"]
    df["Card"] = card_name
    return df[["Transaction Date", "Description", "Amount", "Category", "Card"]]

if __name__ == "__main__":
    # 1) Run individual card scripts
    scripts = ["amex.py", "chase.py", "cap_one.py", "bilt.py"]
    for script in scripts:
        run_script(script)

    # 2) Combine transactions for this year
    today = datetime.date.today()
    year  = today.year
    month = today.month
    month_name = today.strftime("%B")

    cards = [
        {"path": os.path.join(IMPORT_DIR, "AMEX.csv"),   "rename": {"Date": "Transaction Date"},  "name": "American Express Gold",     "credit": False},
        {"path": os.path.join(IMPORT_DIR, "CHASE.csv"),  "rename": {},                              "name": "Chase Sapphire Preferred", "credit": False},
        {"path": os.path.join(IMPORT_DIR, "CAP_ONE.csv"),"rename": {"Debit": "Amount"},           "name": "Venture X",                "credit": True},
        {"path": os.path.join(IMPORT_DIR, "BILT.csv"),   "rename": {},                              "name": "BILT Mastercard",          "credit": False},
    ]

    frames = []
    for cfg in cards:
        df = load_card(cfg["path"], cfg["rename"], cfg["name"], cfg.get("credit", False))
        df = df[df["Transaction Date"].dt.year == year]
        frames.append(df)

    combined = pd.concat(frames).sort_values("Transaction Date")

    # Annual combined file
    annual_out = os.path.join(EXPORT_DIR, str(year), f"Combined_{year}_Expenses.csv")
    os.makedirs(os.path.dirname(annual_out), exist_ok=True)
    combined.to_csv(annual_out, index=False)
    print(f"\nSaved annual combined to {annual_out}")

    # 3) Export per-month combined files
    for m in sorted(combined["Transaction Date"].dt.month.unique()):
        m_name = datetime.date(year, m, 1).strftime("%B")
        dfm = combined[combined["Transaction Date"].dt.month == m]
        monthly_out = os.path.join(EXPORT_DIR, str(year), "Monthly Data", f"combined_{m_name}_{year}_expenses.csv")
        dfm.to_csv(monthly_out, index=False)
        print(f"Exported {m_name}: {monthly_out}")

    # 4) (Optional) Print summary
    print(f"\nMonthly Spend Summary for {year}:")
    monthly_totals = combined.groupby(combined["Transaction Date"].dt.month)["Amount"].sum()
    for m, amt in monthly_totals.items():
        m_name = datetime.date(year, m, 1).strftime("%B")
        print(f"  - {m_name}: ${amt:.2f}")
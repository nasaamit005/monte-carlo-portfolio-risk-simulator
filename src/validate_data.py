
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

raw_path = ROOT / "data" / "raw" / "all_tickers_daily.csv"
prices_path = ROOT / "data" / "processed" / "prices_wide.csv"
returns_path = ROOT / "data" / "processed" / "daily_returns.csv"

data = pd.read_csv(raw_path, parse_dates=["Date"])
prices = pd.read_csv(prices_path, index_col=0, parse_dates=True)
returns = pd.read_csv(returns_path, index_col=0, parse_dates=True)

print("=== DATA QUALITY REPORT ===")
print(f"Raw rows: {len(data):,}")
print(f"Unique tickers: {data['Ticker'].nunique()}")
print(f"Date range: {data['Date'].min().date()} to {data['Date'].max().date()}")
print(f"Duplicate ticker-date rows: {data.duplicated(['Date', 'Ticker']).sum()}")
print(f"Missing raw values:\n{data.isna().sum().to_string()}")
print(f"Non-positive closing prices: {(data['Close'] <= 0).sum()}")
print(f"Price matrix shape: {prices.shape}")
print(f"Missing prices by ticker:\n{prices.isna().sum().to_string()}")
print(f"Missing returns by ticker:\n{returns.isna().sum().to_string()}")
print(f"Infinite returns: {np.isinf(returns.to_numpy()).sum()}")

# Check basic data integrity
assert not data.duplicated(["Date", "Ticker"]).any(), "Duplicate records found"
assert data["Close"].notna().all(), "Missing closing prices found"
assert (data["Close"] > 0).all(), "Non-positive closing prices found"
assert prices.columns.is_unique, "Duplicate price columns found"
assert np.isfinite(returns.dropna().to_numpy()).all(), "Infinite returns found"

print("\nBasic data integrity checks passed.")
print("Review missing prices and returns above before simulation.")


from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = ["AAPL", "AMZN", "GOOGL", "MSFT", "NVDA", "^GSPC"]
ROOT = Path(__file__).resolve().parents[1]


def main():
    (ROOT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)

    frames = []

    for ticker in TICKERS:
        print(f"Downloading {ticker}...")

        df = yf.Ticker(ticker).history(
            period="10y",
            auto_adjust=True
        )

        if df.empty:
            raise RuntimeError(f"No market data returned for {ticker}")

        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df = df.rename_axis("Date").reset_index()
        df["Ticker"] = ticker

        frames.append(
            df[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]]
        )

    data = pd.concat(frames, ignore_index=True)
    data["Date"] = pd.to_datetime(data["Date"]).dt.strftime("%Y-%m-%d")
    data = data.drop_duplicates(["Date", "Ticker"])
    data = data.sort_values(["Date", "Ticker"])

    raw_path = ROOT / "data" / "raw" / "all_tickers_daily.csv"
    data.to_csv(raw_path, index=False)

    prices = data.pivot(
        index="Date", columns="Ticker", values="Close"
    ).sort_index()

    returns = prices.pct_change(fill_method=None)

    prices.to_csv(ROOT / "data" / "processed" / "prices_wide.csv")
    returns.to_csv(ROOT / "data" / "processed" / "daily_returns.csv")

    print("\nDATA DOWNLOAD COMPLETE")
    print(f"Rows downloaded: {len(data):,}")
    print(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
    print(f"Tickers: {', '.join(TICKERS)}")
    print(f"Price matrix shape: {prices.shape}")
    print("Raw data, prices, and returns saved successfully.")


if __name__ == "__main__":
    main()

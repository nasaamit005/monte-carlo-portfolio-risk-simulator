
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRADING_DAYS = 252

STOCKS = ["AAPL", "AMZN", "GOOGL", "MSFT", "NVDA"]
BENCHMARK = "^GSPC"


def main():
    prices = pd.read_csv(
        ROOT / "data" / "processed" / "prices_wide.csv",
        index_col=0,
        parse_dates=True,
    ).sort_index()

    # Use stocks for the portfolio; keep the S&P 500 as benchmark.
    stock_prices = prices[STOCKS]
    returns = stock_prices.pct_change(fill_method=None).dropna()
    benchmark_returns = prices[BENCHMARK].pct_change(fill_method=None).dropna()

    # Equal-weight portfolio: 20% allocated to each stock.
    weights = pd.Series(1 / len(STOCKS), index=STOCKS)
    portfolio_returns = returns.mul(weights, axis=1).sum(axis=1)

    def performance(series):
        series = series.dropna()
        cumulative_return = (1 + series).prod() - 1
        years = len(series) / TRADING_DAYS
        cagr = (1 + cumulative_return) ** (1 / years) - 1
        volatility = series.std(ddof=1) * np.sqrt(TRADING_DAYS)
        annualized_mean = series.mean() * TRADING_DAYS
        sharpe = annualized_mean / volatility if volatility else np.nan

        wealth = (1 + series).cumprod()
        drawdown = wealth / wealth.cummax() - 1

        return {
            "Cumulative Return": cumulative_return,
            "CAGR": cagr,
            "Annualized Mean Return": annualized_mean,
            "Annualized Volatility": volatility,
            "Sharpe Ratio (RF=0)": sharpe,
            "Maximum Drawdown": drawdown.min(),
        }

    results = {
        ticker: performance(returns[ticker])
        for ticker in STOCKS
    }

    results["Equal-Weight Portfolio"] = performance(portfolio_returns)
    results["S&P 500 Benchmark"] = performance(benchmark_returns)

    metrics = pd.DataFrame(results).T
    correlation = returns.corr()

    output_dir = ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(output_dir / "performance_metrics.csv")
    correlation.to_csv(output_dir / "stock_correlation.csv")
    portfolio_returns.rename("Portfolio_Return").to_csv(
        output_dir / "portfolio_daily_returns.csv"
    )

    print("\n=== PERFORMANCE METRICS ===")
    print(metrics.round(4).to_string())
    print("\n=== STOCK CORRELATION MATRIX ===")
    print(correlation.round(3).to_string())
    print("\nSaved:")
    print("data/processed/performance_metrics.csv")
    print("data/processed/stock_correlation.csv")
    print("data/processed/portfolio_daily_returns.csv")


if __name__ == "__main__":
    main()

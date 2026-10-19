
from pathlib import Path
import html

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html

# ============================================================
# MONTE CARLO PORTFOLIO RISK SIMULATOR
# Historical Performance Analytics Dashboard
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
CHARTS = REPORTS / "charts"

REPORTS.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

STOCKS = ["AAPL", "AMZN", "GOOGL", "MSFT", "NVDA"]
BENCHMARK = "^GSPC"
TRADING_DAYS = 252
INITIAL_VALUE = 10_000
RISK_FREE_RATE = 0.0

COLORS = {
    "Portfolio": "#2563EB",
    "^GSPC": "#EA580C",
    "AAPL": "#0891B2",
    "AMZN": "#7C3AED",
    "GOOGL": "#16A34A",
    "MSFT": "#DB2777",
    "NVDA": "#D97706",
}


def safe_ratio(numerator, denominator):
    if pd.isna(denominator) or np.isclose(denominator, 0):
        return np.nan
    return numerator / denominator


def max_drawdown(wealth):
    running_peak = wealth.cummax()
    drawdown = wealth / running_peak - 1
    return drawdown.min(), drawdown


def calculate_metrics(returns, benchmark_returns=None):
    """Calculate historical metrics from a daily return series."""
    r = returns.dropna().astype(float)

    if r.empty:
        raise ValueError("A return series is empty.")

    wealth = (1 + r).cumprod()
    total_return = wealth.iloc[-1] - 1
    years = len(r) / TRADING_DAYS

    cagr = (
        wealth.iloc[-1] ** (1 / years) - 1
        if years > 0 and wealth.iloc[-1] > 0
        else np.nan
    )

    annual_mean = r.mean() * TRADING_DAYS
    annual_vol = r.std(ddof=1) * np.sqrt(TRADING_DAYS)
    daily_rf = (1 + RISK_FREE_RATE) ** (1 / TRADING_DAYS) - 1

    excess = r - daily_rf
    sharpe = safe_ratio(
        excess.mean() * TRADING_DAYS,
        annual_vol
    )

    downside = np.minimum(r - daily_rf, 0)
    downside_dev = np.sqrt(np.mean(downside ** 2)) * np.sqrt(TRADING_DAYS)
    sortino = safe_ratio(
        excess.mean() * TRADING_DAYS,
        downside_dev
    )

    mdd, drawdown = max_drawdown(wealth)
    calmar = safe_ratio(cagr, abs(mdd))

    q95 = r.quantile(0.05)
    q99 = r.quantile(0.01)
    var95 = -q95
    var99 = -q99
    es95 = -r[r <= q95].mean()
    es99 = -r[r <= q99].mean()

    beta = np.nan
    alpha = np.nan
    tracking_error = np.nan
    information_ratio = np.nan

    if benchmark_returns is not None:
        aligned = pd.concat(
            [r.rename("asset"), benchmark_returns.rename("benchmark")],
            axis=1
        ).dropna()

        if len(aligned) > 1:
            market_var = aligned["benchmark"].var(ddof=1)
            beta = safe_ratio(
                aligned["asset"].cov(aligned["benchmark"]),
                market_var
            )
            benchmark_annual_mean = (
                aligned["benchmark"].mean() * TRADING_DAYS
            )
            asset_annual_mean = aligned["asset"].mean() * TRADING_DAYS
            alpha = asset_annual_mean - beta * benchmark_annual_mean

            active = aligned["asset"] - aligned["benchmark"]
            tracking_error = active.std(ddof=1) * np.sqrt(TRADING_DAYS)
            information_ratio = safe_ratio(
                active.mean() * TRADING_DAYS,
                tracking_error
            )

    return {
        "Cumulative Return": total_return,
        "CAGR": cagr,
        "Annualized Mean Return": annual_mean,
        "Annualized Volatility": annual_vol,
        "Sharpe Ratio (RF=0)": sharpe,
        "Sortino Ratio": sortino,
        "Maximum Drawdown": mdd,
        "Calmar Ratio": calmar,
        "Historical VaR 95% (Daily)": var95,
        "Historical VaR 99% (Daily)": var99,
        "Historical ES 95% (Daily)": es95,
        "Historical ES 99% (Daily)": es99,
        "Market Beta": beta,
        "Annualized Alpha (RF=0)": alpha,
        "Tracking Error": tracking_error,
        "Information Ratio": information_ratio,
        "Skewness": r.skew(),
        "Excess Kurtosis": r.kurt(),
        "Positive Days": (r > 0).mean(),
        "Best Day": r.max(),
        "Worst Day": r.min(),
        "Ending Value ($10,000)": INITIAL_VALUE * wealth.iloc[-1],
        "Observations": len(r),
    }


# -------------------- Load data --------------------

price_file = DATA / "prices_wide.csv"

if not price_file.exists():
    raise FileNotFoundError(
        f"Could not find {price_file}. Run your data preparation scripts first."
    )

prices = pd.read_csv(
    price_file,
    index_col=0,
    parse_dates=True
).sort_index()

required = STOCKS + [BENCHMARK]
missing = [ticker for ticker in required if ticker not in prices.columns]

if missing:
    raise ValueError(f"Missing price columns in prices_wide.csv: {missing}")

prices = prices[required].apply(pd.to_numeric, errors="coerce")
prices = prices.replace([np.inf, -np.inf], np.nan)
prices = prices.dropna(how="all")

# Use common complete observations to make comparisons consistent.
prices = prices.dropna(subset=required)

if len(prices) < 2:
    raise ValueError("Not enough complete price observations to analyze.")

returns = prices.pct_change(fill_method=None).dropna()

# Simple daily equal-weight return series.
# This represents daily equal-weight returns, not transaction-cost-aware trading.
portfolio_returns = returns[STOCKS].mean(axis=1).rename("Portfolio")
benchmark_returns = returns[BENCHMARK].rename(BENCHMARK)

asset_returns = returns[STOCKS + [BENCHMARK]].copy()
asset_returns["Portfolio"] = portfolio_returns

# Use the first valid return date as the start of the performance series.
wealth = (1 + asset_returns).cumprod() * INITIAL_VALUE
wealth.index.name = "Date"

# -------------------- Metrics table --------------------

rows = {}
for asset in STOCKS + ["Portfolio", BENCHMARK]:
    benchmark_for_comparison = (
        benchmark_returns if asset != BENCHMARK else None
    )
    rows[asset] = calculate_metrics(
        asset_returns[asset],
        benchmark_for_comparison
    )

metrics = pd.DataFrame.from_dict(rows, orient="index")
metrics.index.name = "Asset / Portfolio"

metrics.to_csv(REPORTS / "advanced_performance_metrics.csv")

corr = returns[STOCKS].corr()
corr.to_csv(REPORTS / "stock_correlation.csv")

# Additional data exports for reuse.
asset_returns.to_csv(REPORTS / "daily_asset_and_portfolio_returns.csv")
wealth.to_csv(REPORTS / "growth_of_10000.csv")

# -------------------- Formatting helpers --------------------

percent_metrics = {
    "Cumulative Return", "CAGR", "Annualized Mean Return",
    "Annualized Volatility", "Maximum Drawdown",
    "Historical VaR 95% (Daily)", "Historical VaR 99% (Daily)",
    "Historical ES 95% (Daily)", "Historical ES 99% (Daily)",
    "Tracking Error", "Positive Days", "Best Day", "Worst Day",
}

ratio_metrics = {
    "Sharpe Ratio (RF=0)", "Sortino Ratio", "Calmar Ratio",
    "Market Beta", "Annualized Alpha (RF=0)", "Information Ratio",
    "Skewness", "Excess Kurtosis",
}


def format_metric(column, value):
    if pd.isna(value):
        return "N/A"
    if column in percent_metrics:
        return f"{value:.2%}"
    if column in ratio_metrics:
        return f"{value:.3f}"
    if column == "Ending Value ($10,000)":
        return f"${value:,.2f}"
    if column == "Observations":
        return f"{int(value):,}"
    return f"{value:,.3f}"


table_columns = [
    "Cumulative Return",
    "CAGR",
    "Annualized Mean Return",
    "Annualized Volatility",
    "Sharpe Ratio (RF=0)",
    "Sortino Ratio",
    "Maximum Drawdown",
    "Calmar Ratio",
    "Historical VaR 95% (Daily)",
    "Historical VaR 99% (Daily)",
    "Historical ES 95% (Daily)",
    "Historical ES 99% (Daily)",
    "Market Beta",
    "Annualized Alpha (RF=0)",
    "Tracking Error",
    "Information Ratio",
    "Skewness",
    "Excess Kurtosis",
    "Positive Days",
    "Best Day",
    "Worst Day",
    "Ending Value ($10,000)",
    "Observations",
]

formatted = metrics[table_columns].copy()
for column in formatted.columns:
    formatted[column] = formatted[column].map(
        lambda value, col=column: format_metric(col, value)
    )

# -------------------- Chart helpers --------------------

chart_fragments = []


def save_chart(fig, filename, title, description):
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left"),
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", color="#1F2937", size=12),
        margin=dict(l=55, r=30, t=80, b=55),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0),
    )
    fig.write_html(
        CHARTS / filename,
        include_plotlyjs=True,
        full_html=True
    )
    chart_fragments.append(
        f"""
        <section class="chart-card">
          <h2>{html.escape(title)}</h2>
          <p class="description">{html.escape(description)}</p>
          {to_html(fig, full_html=False, include_plotlyjs=False,
                   config={"responsive": True, "displaylogo": False})}
          <p><a href="charts/{html.escape(filename)}" target="_blank">
          Open this chart separately</a></p>
        </section>
        """
    )


# 1. Growth of $10,000
fig = go.Figure()
for asset in ["Portfolio", BENCHMARK] + STOCKS:
    fig.add_trace(go.Scatter(
        x=wealth.index,
        y=wealth[asset],
        mode="lines",
        name=asset,
        line=dict(color=COLORS.get(asset), width=2.5 if asset == "Portfolio" else 1.6),
        hovertemplate="%{x|%Y-%m-%d}<br>$%{y:,.2f}<extra>%{fullData.name}</extra>",
    ))
fig.update_layout(
    yaxis_title="Portfolio value ($)",
    xaxis_title="Date",
    yaxis=dict(tickprefix="$", separatethousands=True),
)
save_chart(
    fig, "growth_of_10000.html", "Growth of $10,000",
    "Historical growth assuming returns are reinvested. Past performance does not predict future returns."
)

# 2. Cumulative return comparison
cumulative = wealth / INITIAL_VALUE - 1
fig = go.Figure()
for asset in ["Portfolio", BENCHMARK] + STOCKS:
    fig.add_trace(go.Scatter(
        x=cumulative.index, y=cumulative[asset] * 100,
        mode="lines", name=asset,
        line=dict(color=COLORS.get(asset), width=2.4 if asset == "Portfolio" else 1.5),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}%<extra>%{fullData.name}</extra>",
    ))
fig.update_layout(xaxis_title="Date", yaxis_title="Cumulative return (%)")
save_chart(
    fig, "cumulative_returns.html", "Cumulative Return Comparison",
    "Cumulative return from the common starting date, excluding deposits and withdrawals."
)

# 3. Risk-return scatter
scatter_data = metrics.reset_index()
fig = px.scatter(
    scatter_data,
    x="Annualized Volatility",
    y="CAGR",
    text="Asset / Portfolio",
    color="Asset / Portfolio",
    color_discrete_map=COLORS,
    hover_data=["Sharpe Ratio (RF=0)", "Maximum Drawdown", "Sortino Ratio"],
)
fig.update_traces(textposition="top center", marker=dict(size=13))
fig.update_layout(
    xaxis_title="Annualized volatility",
    yaxis_title="CAGR",
    xaxis_tickformat=".0%",
    yaxis_tickformat=".0%",
    showlegend=False,
)
save_chart(
    fig, "risk_return_comparison.html", "Risk–Return Comparison",
    "Compares historical compound growth with annualized volatility. This is descriptive, not an optimization result."
)

# 4. Drawdown history
fig = go.Figure()
for asset in ["Portfolio", BENCHMARK] + STOCKS:
    running_peak = wealth[asset].cummax()
    dd = wealth[asset] / running_peak - 1
    fig.add_trace(go.Scatter(
        x=dd.index, y=dd * 100, mode="lines", name=asset,
        line=dict(color=COLORS.get(asset), width=2.2 if asset == "Portfolio" else 1.3),
        hovertemplate="%{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra>%{fullData.name}</extra>",
    ))
fig.update_layout(xaxis_title="Date", yaxis_title="Drawdown (%)")
save_chart(
    fig, "drawdown_history.html", "Historical Drawdowns",
    "Drawdown is measured from each series' prior running peak."
)

# 5. Rolling 21-trading-day annualized volatility
rolling_vol = returns[STOCKS].copy()
rolling_vol["Portfolio"] = portfolio_returns
rolling_vol[BENCHMARK] = benchmark_returns
rolling_vol = rolling_vol.rolling(21).std() * np.sqrt(TRADING_DAYS)
fig = go.Figure()
for asset in ["Portfolio", BENCHMARK] + STOCKS:
    fig.add_trace(go.Scatter(
        x=rolling_vol.index, y=rolling_vol[asset] * 100,
        mode="lines", name=asset,
        line=dict(color=COLORS.get(asset), width=2.2 if asset == "Portfolio" else 1.3),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}%<extra>%{fullData.name}</extra>",
    ))
fig.update_layout(xaxis_title="Date", yaxis_title="Annualized volatility (%)")
save_chart(
    fig, "rolling_volatility.html", "Rolling 21-Day Annualized Volatility",
    "Short-window volatility can change quickly and should not be interpreted as a forecast."
)

# 6. Correlation heatmap
fig = px.imshow(
    corr, text_auto=".2f", zmin=-1, zmax=1,
    color_continuous_scale="RdBu_r", aspect="auto",
)
fig.update_layout(xaxis_title="Asset", yaxis_title="Asset")
save_chart(
    fig, "correlation_heatmap.html", "Stock Return Correlation",
    "Correlation is based on historical daily stock returns. Correlation can rise during market stress."
)

# 7. Daily return distributions
long_returns = returns[STOCKS].copy()
long_returns["Portfolio"] = portfolio_returns
long_returns = long_returns.melt(
    var_name="Asset", value_name="Daily Return"
)
fig = px.histogram(
    long_returns, x="Daily Return", color="Asset",
    histnorm="probability density", opacity=0.58,
    marginal="box", barmode="overlay",
    color_discrete_map=COLORS,
)
fig.update_layout(
    xaxis_title="Daily return",
    yaxis_title="Probability density",
    xaxis_tickformat=".1%",
)
save_chart(
    fig, "daily_return_distributions.html", "Daily Return Distributions",
    "The distributions show historical daily returns and tails; they do not establish a future probability model."
)

# 8. Monthly portfolio returns heatmap
monthly_returns = (1 + portfolio_returns).resample("ME").prod() - 1
monthly_df = monthly_returns.to_frame("Return")
monthly_df["Year"] = monthly_df.index.year
monthly_df["Month"] = monthly_df.index.month
monthly_pivot = monthly_df.pivot(
    index="Year", columns="Month", values="Return"
).reindex(columns=range(1, 13))
monthly_pivot.columns = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]
fig = px.imshow(
    monthly_pivot * 100,
    text_auto=".1f",
    color_continuous_scale="RdYlGn",
    color_continuous_midpoint=0,
    aspect="auto",
)
fig.update_layout(xaxis_title="Month", yaxis_title="Year",
                  coloraxis_colorbar_title="Return (%)")
save_chart(
    fig, "monthly_returns_heatmap.html", "Portfolio Monthly Returns",
    "Monthly returns are compounded from daily equal-weight portfolio returns."
)

# -------------------- Dashboard HTML --------------------

portfolio = metrics.loc["Portfolio"]
benchmark = metrics.loc[BENCHMARK]


def card(label, value, note):
    return f"""
    <div class="kpi">
      <div class="kpi-label">{html.escape(label)}</div>
      <div class="kpi-value">{html.escape(value)}</div>
      <div class="kpi-note">{html.escape(note)}</div>
    </div>
    """


kpis = [
    ("Portfolio CAGR", format_metric("CAGR", portfolio["CAGR"]),
     "Historical annualized compound growth"),
    ("Annualized Volatility", format_metric("Annualized Volatility", portfolio["Annualized Volatility"]),
     "Annualized standard deviation"),
    ("Sharpe Ratio", format_metric("Sharpe Ratio (RF=0)", portfolio["Sharpe Ratio (RF=0)"]),
     "Risk-free rate assumed to be 0%"),
    ("Maximum Drawdown", format_metric("Maximum Drawdown", portfolio["Maximum Drawdown"]),
     "Worst peak-to-trough decline"),
    ("Historical Daily VaR 95%", format_metric("Historical VaR 95% (Daily)", portfolio["Historical VaR 95% (Daily)"]),
     "Historical daily loss threshold"),
    ("Historical Daily ES 95%", format_metric("Historical ES 95% (Daily)", portfolio["Historical ES 95% (Daily)"]),
     "Average loss in the worst 5% tail"),
    ("Ending Value", format_metric("Ending Value ($10,000)", portfolio["Ending Value ($10,000)"]),
     "Illustrative $10,000 investment"),
]

kpi_html = "".join(card(*item) for item in kpis)

table_headers = ["Asset / Portfolio"] + list(formatted.columns)
table_rows = []
for asset, row in formatted.iterrows():
    cells = "".join(f"<td>{html.escape(str(value))}</td>" for value in row)
    table_rows.append(
        f"<tr><th scope='row'>{html.escape(str(asset))}</th>{cells}</tr>"
    )

table_html = f"""
<div class="table-wrap">
<table>
<thead><tr>{''.join(f'<th>{html.escape(str(c))}</th>' for c in table_headers)}</tr></thead>
<tbody>{''.join(table_rows)}</tbody>
</table>
</div>
"""

portfolio_cagr = portfolio["CAGR"]
benchmark_cagr = benchmark["CAGR"]
portfolio_mdd = portfolio["Maximum Drawdown"]
benchmark_mdd = benchmark["Maximum Drawdown"]

findings = [
    f"Portfolio CAGR: {format_metric('CAGR', portfolio_cagr)}.",
    f"S&P 500 benchmark CAGR: {format_metric('CAGR', benchmark_cagr)}.",
    f"Portfolio maximum drawdown: {format_metric('Maximum Drawdown', portfolio_mdd)}.",
    f"S&P 500 benchmark maximum drawdown: {format_metric('Maximum Drawdown', benchmark_mdd)}.",
    f"Portfolio annualized volatility: {format_metric('Annualized Volatility', portfolio['Annualized Volatility'])}.",
    f"Portfolio Sharpe ratio with a zero risk-free rate: {format_metric('Sharpe Ratio (RF=0)', portfolio['Sharpe Ratio (RF=0)'])}.",
]

findings_html = "".join(f"<li>{html.escape(item)}</li>" for item in findings)

dashboard = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Risk & Performance Analytics</title>
<script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
<style>
:root {{
  --ink: #172033; --muted: #64748b; --line: #e2e8f0;
  --panel: #ffffff; --bg: #f4f7fb; --blue: #1d4ed8;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: Arial, Helvetica, sans-serif; line-height: 1.55;
}}
header {{
  padding: 36px max(22px, calc((100vw - 1440px) / 2));
  background: linear-gradient(120deg, #eff6ff, #ffffff);
  border-bottom: 1px solid var(--line);
}}
header h1 {{ margin: 0 0 8px; font-size: clamp(26px, 4vw, 38px); }}
header p {{ margin: 4px 0; color: var(--muted); }}
main {{ max-width: 1440px; padding: 24px; margin: auto; }}
h2 {{ font-size: 21px; margin: 0 0 12px; }}
.section {{ margin: 26px 0; }}
.kpis {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 14px; margin-top: 22px;
}}
.kpi, .panel, .chart-card {{
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 14px; box-shadow: 0 4px 16px rgba(15, 23, 42, .045);
}}
.kpi {{ padding: 18px; }}
.kpi-label {{ font-size: 13px; color: var(--muted); font-weight: 700; }}
.kpi-value {{ font-size: 26px; font-weight: 750; margin: 7px 0; }}
.kpi-note, .description, .muted {{ color: var(--muted); font-size: 13px; }}
.panel {{ padding: 20px; overflow: hidden; }}
.table-wrap {{ overflow-x: auto; max-height: 650px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 12px; white-space: nowrap; }}
th, td {{ padding: 11px 13px; text-align: right; border-bottom: 1px solid var(--line); }}
thead th {{ position: sticky; top: 0; background: #1d4ed8; color: white; z-index: 1; }}
tbody th {{ text-align: left; background: #eff6ff; }}
tbody tr:nth-child(even) td {{ background: #f8fafc; }}
.chart-card {{ padding: 20px; margin: 18px 0; overflow: hidden; }}
.chart-card h2 {{ margin-bottom: 4px; }}
a {{ color: var(--blue); }}
.warning {{
  padding: 16px; border-left: 4px solid #d97706;
  background: #fffbeb; border-radius: 8px;
}}
footer {{ color: var(--muted); padding: 24px 0 40px; font-size: 12px; }}
@media (max-width: 600px) {{ main {{ padding: 14px; }} .kpi-value {{ font-size: 22px; }} }}
</style>
</head>
<body>
<header>
  <h1>Portfolio Risk &amp; Performance Analytics</h1>
  <p>Interactive historical analysis | Equal-weight five-stock portfolio | S&amp;P 500 benchmark</p>
  <p>Sample: {prices.index.min():%d %b %Y} – {prices.index.max():%d %b %Y} |
     {len(returns):,} daily return observations</p>
</header>
<main>
  <section class="section">
    <h2>Executive risk dashboard</h2>
    <div class="kpis">{kpi_html}</div>
  </section>

  <section class="section panel">
    <h2>Detailed performance and risk comparison</h2>
    <p class="muted">Returns and risk metrics are historical estimates. VaR and ES are daily historical measures.</p>
    {table_html}
  </section>

  <section class="section panel">
    <h2>Computed highlights</h2>
    <ul>{findings_html}</ul>
    <p class="muted">These highlights are generated from this dataset, not from target or advertised performance.</p>
  </section>

  {''.join(chart_fragments)}

  <section class="section panel">
    <h2>Methodology and limitations</h2>
    <ul>
      <li>Daily returns are calculated from the adjusted-price series provided in prices_wide.csv.</li>
      <li>The portfolio is the arithmetic equal-weight average of the five stock daily returns.</li>
      <li>Annualization uses 252 trading days. CAGR uses the number of daily observations divided by 252.</li>
      <li>Sharpe ratio assumes a 0% annual risk-free rate for this baseline.</li>
      <li>Historical 95% and 99% VaR are positive loss thresholds based on the 5th and 1st return percentiles.</li>
      <li>Expected Shortfall is the average loss among observations at or below the corresponding return percentile.</li>
      <li>Alpha is an annualized arithmetic-return estimate with a 0% risk-free rate, not a factor-model alpha.</li>
      <li>The benchmark is the S&amp;P 500 index series. The portfolio and index may have different investability and dividend conventions depending on the input data.</li>
      <li>No taxes, transaction costs, slippage, financing costs, or execution constraints are included.</li>
      <li>This is historical analytics, not the Monte Carlo simulation stage and not investment advice.</li>
    </ul>
  </section>

  <section class="section panel">
    <h2>Research foundations</h2>
    <ul>
      <li>Markowitz (1952), <em>Portfolio Selection</em> — <a href="https://doi.org/10.1111/j.1540-6261.1952.tb01525.x" target="_blank" rel="noopener">Journal of Finance</a>.</li>
      <li>Artzner et al. (1999), <em>Coherent Measures of Risk</em> — <a href="https://doi.org/10.1111/1467-9965.00068" target="_blank" rel="noopener">Mathematical Finance</a>.</li>
      <li>Acerbi &amp; Tasche (2002), <em>On the Coherence of Expected Shortfall</em> — <a href="https://doi.org/10.1016/S0378-4266(02)00283-2" target="_blank" rel="noopener">Journal of Banking &amp; Finance</a>.</li>
      <li>Glasserman (2003), <em>Monte Carlo Methods in Financial Engineering</em> — <a href="https://doi.org/10.1007/978-0-387-21617-1" target="_blank" rel="noopener">Springer</a>.</li>
    </ul>
  </section>
  <footer>
    Generated by create_interactive_report.py. Use the links below each chart to open an individual interactive HTML file.
  </footer>
</main>
</body>
</html>
"""

dashboard_file = REPORTS / "interactive_performance_dashboard.html"
dashboard_file.write_text(dashboard, encoding="utf-8")

# A compact plain-text summary for version control and review.
summary_lines = [
    "# Historical Portfolio Performance Summary",
    "",
    f"- Price sample: {prices.index.min().date()} to {prices.index.max().date()}",
    f"- Daily return observations: {len(returns):,}",
    f"- Portfolio CAGR: {format_metric('CAGR', portfolio_cagr)}",
    f"- Benchmark CAGR: {format_metric('CAGR', benchmark_cagr)}",
    f"- Portfolio maximum drawdown: {format_metric('Maximum Drawdown', portfolio_mdd)}",
    f"- Benchmark maximum drawdown: {format_metric('Maximum Drawdown', benchmark_mdd)}",
    f"- Portfolio annualized volatility: {format_metric('Annualized Volatility', portfolio['Annualized Volatility'])}",
    f"- Portfolio Sharpe ratio: {format_metric('Sharpe Ratio (RF=0)', portfolio['Sharpe Ratio (RF=0)'])}",
    "",
    "## Interpretation notes",
    "- Results are historical and depend on the selected sample and data conventions.",
    "- VaR and Expected Shortfall are historical daily loss estimates, not maximum-loss guarantees.",
    "- The portfolio is daily equal-weighted at the return-series level.",
    "- Monte Carlo forward simulations will be implemented separately.",
]
(REPORTS / "historical_analysis_summary.md").write_text(
    "\n".join(summary_lines) + "\n",
    encoding="utf-8"
)

print("\nREPORT GENERATION COMPLETE")
print(f"Dashboard: {dashboard_file}")
print(f"Individual charts: {CHARTS}")
print(f"Metrics CSV: {REPORTS / 'advanced_performance_metrics.csv'}")
print(f"Correlation CSV: {REPORTS / 'stock_correlation.csv'}")
print(f"Daily returns CSV: {REPORTS / 'daily_asset_and_portfolio_returns.csv'}")
print(f"Growth of $10,000 CSV: {REPORTS / 'growth_of_10000.csv'}")
print(f"Summary: {REPORTS / 'historical_analysis_summary.md'}")
print(f"\nPortfolio CAGR: {format_metric('CAGR', portfolio_cagr)}")
print(f"Portfolio max drawdown: {format_metric('Maximum Drawdown', portfolio_mdd)}") 

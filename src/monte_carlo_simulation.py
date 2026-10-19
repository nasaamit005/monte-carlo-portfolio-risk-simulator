
from pathlib import Path
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# CONFIGURATION
# ============================================================
ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "processed" / "prices_wide.csv"
OUTPUT_DIR = ROOT / "reports" / "monte_carlo"
CHART_DIR = OUTPUT_DIR / "charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

N_SIMULATIONS = 10_000
HORIZON_DAYS = 252
INITIAL_PORTFOLIO = 10_000.0
RANDOM_SEED = 42
CONFIDENCE_LEVELS = (0.95, 0.99)

ASSETS = ["AAPL", "AMZN", "GOOGL", "MSFT", "NVDA"]
BENCHMARK = "^GSPC"


# ============================================================
# INPUT VALIDATION
# ============================================================
def validate_configuration():
    """Validate simulation settings before doing any work."""
    if (
        isinstance(N_SIMULATIONS, bool)
        or not isinstance(N_SIMULATIONS, (int, np.integer))
        or N_SIMULATIONS <= 0
    ):
        raise ValueError("N_SIMULATIONS must be a positive integer.")

    if (
        isinstance(HORIZON_DAYS, bool)
        or not isinstance(HORIZON_DAYS, (int, np.integer))
        or HORIZON_DAYS <= 0
    ):
        raise ValueError("HORIZON_DAYS must be a positive integer.")

    if (
        not np.isfinite(INITIAL_PORTFOLIO)
        or INITIAL_PORTFOLIO <= 0
    ):
        raise ValueError("INITIAL_PORTFOLIO must be finite and positive.")

    if not ASSETS or len(set(ASSETS)) != len(ASSETS):
        raise ValueError("ASSETS must be a non-empty list of unique tickers.")

    if (
        not CONFIDENCE_LEVELS
        or any(
            not np.isfinite(level) or not 0 < level < 1
            for level in CONFIDENCE_LEVELS
        )
    ):
        raise ValueError(
            "Every confidence level must be strictly between 0 and 1."
        )


# ============================================================
# LOAD AND VALIDATE PRICE DATA
# ============================================================
def load_data():
    """Load historical prices and validate the required stock columns."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Price data not found: {DATA_FILE}\n"
            "Run your existing data preparation steps first."
        )

    prices = pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)

    if prices.empty:
        raise ValueError("The historical price dataset is empty.")

    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("The first column must contain valid dates.")

    if prices.index.isna().any():
        raise ValueError("The price dataset contains invalid dates.")

    prices = prices.sort_index()
    prices = prices[~prices.index.duplicated(keep="last")]

    missing_assets = [asset for asset in ASSETS if asset not in prices.columns]

    if missing_assets:
        raise ValueError(
            f"Missing expected stock columns: {missing_assets}\n"
            f"Available columns: {list(prices.columns)}"
        )

    prices = prices[ASSETS].apply(pd.to_numeric, errors="coerce")

    # Remove rows that have missing or non-finite prices for any asset.
    prices = prices.replace([np.inf, -np.inf], np.nan)
    prices = prices.dropna(how="any")

    if len(prices) < 101:
        raise ValueError(
            "At least 101 complete price observations are required "
            "to estimate returns."
        )

    if (prices <= 0).any().any():
        raise ValueError(
            "Prices must be strictly positive to calculate log returns."
        )

    return prices, list(ASSETS)


# ============================================================
# COVARIANCE MATRIX VALIDATION
# ============================================================
def make_positive_semidefinite(covariance):
    """
    Symmetrize a covariance matrix and clip negative eigenvalues.

    This numerical adjustment makes the matrix positive semidefinite
    up to floating-point precision.
    """
    covariance = np.asarray(covariance, dtype=float)

    if covariance.ndim != 2:
        raise ValueError("Covariance must be a two-dimensional matrix.")

    if covariance.shape[0] == 0 or covariance.shape[0] != covariance.shape[1]:
        raise ValueError("Covariance must be a non-empty square matrix.")

    if not np.isfinite(covariance).all():
        raise ValueError("Covariance must contain only finite numbers.")

    covariance = (covariance + covariance.T) / 2.0

    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    eigenvalues = np.clip(eigenvalues, 0.0, None)

    corrected = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

    # Remove minor asymmetry caused by floating-point arithmetic.
    corrected = (corrected + corrected.T) / 2.0

    if not np.isfinite(corrected).all():
        raise ValueError("Covariance correction produced non-finite values.")

    return corrected


# ============================================================
# VALUE AT RISK AND EXPECTED SHORTFALL
# ============================================================
def calculate_risk_metrics(terminal_values, initial_value):
    """Calculate horizon VaR and Expected Shortfall from terminal outcomes."""
    terminal_values = np.asarray(terminal_values, dtype=float)

    if terminal_values.ndim != 1 or terminal_values.size == 0:
        raise ValueError(
            "Terminal values must be a non-empty one-dimensional array."
        )

    if not np.isfinite(terminal_values).all():
        raise ValueError(
            "Terminal values must contain only finite numbers."
        )

    if (terminal_values < 0).any():
        raise ValueError("Terminal values cannot be negative.")

    if (
        isinstance(initial_value, (bool, np.bool_))
        or not np.isscalar(initial_value)
        or not np.isfinite(initial_value)
        or initial_value <= 0
    ):
        raise ValueError(
            "Initial portfolio value must be finite and positive."
        )

    initial_value = float(initial_value)
    terminal_returns = terminal_values / initial_value - 1.0

    metrics = []

    for confidence in CONFIDENCE_LEVELS:
        lower_quantile = float(
            np.quantile(terminal_returns, 1.0 - confidence)
        )

        tail_returns = terminal_returns[
            terminal_returns <= lower_quantile
        ]

        if tail_returns.size == 0:
            raise ValueError(
                f"No tail observations available at confidence {confidence:.0%}."
            )

        expected_shortfall_return = float(tail_returns.mean())

        metrics.append({
            "Confidence_Level": confidence,
            "VaR_Return_Threshold": lower_quantile,
            "VaR_Loss_Percent": -lower_quantile * 100.0,
            "VaR_Loss_Amount": -lower_quantile * initial_value,
            "Expected_Shortfall_Loss_Percent": (
                -expected_shortfall_return * 100.0
            ),
            "Expected_Shortfall_Loss_Amount": (
                -expected_shortfall_return * initial_value
            ),
            "Tail_Simulation_Count": int(tail_returns.size),
        })

    return pd.DataFrame(metrics)


# ============================================================
# PLOTLY CHART UTILITIES
# ============================================================
def save_chart(fig, filename):
    """Save a standalone interactive Plotly HTML chart."""
    path = CHART_DIR / filename
    fig.write_html(
        str(path),
        include_plotlyjs=True,
        full_html=True,
    )
    print(f"Chart saved: {path}")


def apply_chart_layout(fig, title):
    """Apply consistent light styling and interactive hover behavior."""
    fig.update_layout(
        title=title,
        title_x=0.5,
        template="plotly_white",
        hovermode="closest",
        margin=dict(l=70, r=35, t=85, b=65),
        font=dict(family="Arial", size=12),
    )
    return fig


# ============================================================
# MAIN SIMULATION
# ============================================================
def main():
    validate_configuration()

    # --------------------------------------------------------
    # 1. Prepare historical returns
    # --------------------------------------------------------
    prices, assets = load_data()

    log_returns = np.log(prices / prices.shift(1)).dropna()

    if len(log_returns) < 100:
        raise ValueError("Insufficient daily return observations.")

    if not np.isfinite(log_returns.to_numpy()).all():
        raise ValueError("Historical returns contain non-finite values.")

    mean_daily = log_returns.mean().to_numpy(dtype=float)
    covariance_daily = make_positive_semidefinite(
        log_returns.cov().to_numpy(dtype=float)
    )

    if not np.isfinite(mean_daily).all():
        raise ValueError("Historical mean returns contain non-finite values.")

    asset_weights = np.full(len(assets), 1.0 / len(assets))

    # --------------------------------------------------------
    # 2. Simulate correlated daily log returns
    # Shape: simulations x days x assets
    # --------------------------------------------------------
    rng = np.random.default_rng(RANDOM_SEED)

    simulated_log_returns = rng.multivariate_normal(
        mean=mean_daily,
        cov=covariance_daily,
        size=(N_SIMULATIONS, HORIZON_DAYS),
        check_valid="raise",
        method="svd",
    )

    if not np.isfinite(simulated_log_returns).all():
        raise ValueError("Simulated log returns contain non-finite values.")

    # Convert simulated log returns to simple returns.
    with np.errstate(over="raise", invalid="raise"):
        try:
            simulated_asset_returns = np.expm1(simulated_log_returns)
        except FloatingPointError as exc:
            raise ValueError(
                "Simulated returns overflowed numerically. "
                "Review historical data and model assumptions."
            ) from exc

    # Equal-weighted portfolio rebalanced daily.
    simulated_portfolio_returns = np.einsum(
        "sda,a->sd",
        simulated_asset_returns,
        asset_weights,
    )

    if not np.isfinite(simulated_portfolio_returns).all():
        raise ValueError(
            "Non-finite portfolio returns occurred. "
            "Review historical data and simulation assumptions."
        )

    # With daily rebalancing, each asset return is weighted each day.
    # Reject a simulated daily portfolio loss below -100%.
    if (simulated_portfolio_returns < -1.0).any():
        raise ValueError(
            "A simulated daily portfolio return was below -100%. "
            "The simple-return wealth model is not valid for this outcome."
        )

    # Calculate wealth paths while detecting overflow.
    with np.errstate(over="raise", invalid="raise"):
        try:
            wealth_paths = INITIAL_PORTFOLIO * np.cumprod(
                1.0 + simulated_portfolio_returns,
                axis=1,
            )
        except FloatingPointError as exc:
            raise ValueError(
                "Simulated wealth paths overflowed numerically."
            ) from exc

    if not np.isfinite(wealth_paths).all():
        raise ValueError("Wealth paths contain non-finite values.")

    terminal_values = wealth_paths[:, -1]
    terminal_returns = terminal_values / INITIAL_PORTFOLIO - 1.0

    # --------------------------------------------------------
    # 3. Calculate risk and summary statistics
    # --------------------------------------------------------
    metrics = calculate_risk_metrics(
        terminal_values,
        INITIAL_PORTFOLIO,
    )

    summary = {
        "Simulation_Count": N_SIMULATIONS,
        "Horizon_Trading_Days": HORIZON_DAYS,
        "Initial_Portfolio_Value": INITIAL_PORTFOLIO,
        "Portfolio_Construction": "Equal-weighted; daily rebalancing",
        "Assets": ", ".join(assets),
        "Random_Seed": RANDOM_SEED,
        "Historical_Return_Observations": int(len(log_returns)),
        "Historical_Start_Date": prices.index.min().strftime("%Y-%m-%d"),
        "Historical_End_Date": prices.index.max().strftime("%Y-%m-%d"),
        "Mean_Terminal_Value": float(np.mean(terminal_values)),
        "Median_Terminal_Value": float(np.median(terminal_values)),
        "5th_Percentile_Terminal_Value": float(
            np.quantile(terminal_values, 0.05)
        ),
        "95th_Percentile_Terminal_Value": float(
            np.quantile(terminal_values, 0.95)
        ),
        "Probability_Of_Loss_Percent": float(
            np.mean(terminal_returns < 0.0) * 100.0
        ),
        "Probability_Below_Initial_Value_Percent": float(
            np.mean(terminal_values < INITIAL_PORTFOLIO) * 100.0
        ),
        "Worst_Simulated_Terminal_Value": float(np.min(terminal_values)),
        "Best_Simulated_Terminal_Value": float(np.max(terminal_values)),
    }

    # --------------------------------------------------------
    # 4. Save tabular and configuration outputs
    # --------------------------------------------------------
    pd.DataFrame([summary]).to_csv(
        OUTPUT_DIR / "simulation_summary.csv",
        index=False,
    )

    metrics.to_csv(
        OUTPUT_DIR / "simulated_var_es.csv",
        index=False,
    )

    pd.DataFrame({
        "Simulation": np.arange(1, N_SIMULATIONS + 1),
        "Terminal_Value": terminal_values,
        "Terminal_Return_Percent": terminal_returns * 100.0,
        "Profit_Loss": terminal_values - INITIAL_PORTFOLIO,
    }).to_csv(
        OUTPUT_DIR / "terminal_values.csv",
        index=False,
    )

    # Save a manageable sample of wealth paths.
    path_count = min(100, N_SIMULATIONS)

    path_frame = pd.DataFrame(
        wealth_paths[:path_count].T,
        index=np.arange(1, HORIZON_DAYS + 1),
        columns=[
            f"Simulation_{i + 1}"
            for i in range(path_count)
        ],
    )
    path_frame.index.name = "Trading_Day"

    path_frame.to_csv(
        OUTPUT_DIR / "sample_simulation_paths.csv"
    )

    # Save the same number of sample daily-return paths.
    returns_frame = pd.DataFrame(
        simulated_portfolio_returns[:path_count].T,
        index=np.arange(1, HORIZON_DAYS + 1),
        columns=[
            f"Simulation_{i + 1}"
            for i in range(path_count)
        ],
    )
    returns_frame.index.name = "Trading_Day"

    returns_frame.to_csv(
        OUTPUT_DIR / "sample_simulated_daily_returns.csv"
    )

    configuration = {
        **summary,
        "Model": "Multivariate normal daily log-return model",
        "Return_Estimation": "Historical sample mean and covariance",
        "Portfolio_Weights": {
            asset: float(weight)
            for asset, weight in zip(assets, asset_weights)
        },
        "Benchmark_Column_Detected": BENCHMARK in pd.read_csv(
            DATA_FILE, nrows=0
        ).columns,
        "Limitations": [
            "Assumes historical mean and covariance remain representative.",
            "Does not explicitly model fat tails or changing volatility.",
            "Does not include transaction costs, taxes, or slippage.",
            "Assumes daily rebalancing to equal weights.",
            "Monte Carlo results are model-based scenarios, not forecasts.",
        ],
    }

    with open(
        OUTPUT_DIR / "simulation_configuration.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(configuration, file, indent=2, allow_nan=False)

    # --------------------------------------------------------
    # 5. Interactive chart: terminal portfolio values
    # --------------------------------------------------------
    fig = px.histogram(
        x=terminal_values,
        nbins=80,
        title="Monte Carlo: Distribution of Terminal Portfolio Values",
        labels={
            "x": "Portfolio Value at Horizon ($)",
            "y": "Number of Simulations",
        },
        template="plotly_white",
        opacity=0.82,
    )

    fig.add_vline(
        x=INITIAL_PORTFOLIO,
        line_dash="dash",
        line_width=2,
        annotation_text=f"Initial ${INITIAL_PORTFOLIO:,.0f}",
    )

    fig.add_vline(
        x=float(np.median(terminal_values)),
        line_dash="dot",
        line_width=2,
        annotation_text=f"Median ${np.median(terminal_values):,.0f}",
    )

    fig.update_layout(
        bargap=0.05,
        hovermode="x",
    )
    apply_chart_layout(
        fig,
        "Monte Carlo: Distribution of Terminal Portfolio Values",
    )
    save_chart(fig, "terminal_value_distribution.html")

    # --------------------------------------------------------
    # 6. Interactive chart: sample simulated paths
    # --------------------------------------------------------
    path_df = path_frame.reset_index().melt(
        id_vars="Trading_Day",
        var_name="Simulation",
        value_name="Portfolio_Value",
    )

    fig = px.line(
        path_df,
        x="Trading_Day",
        y="Portfolio_Value",
        color="Simulation",
        title="Monte Carlo: Sample Portfolio Paths",
        labels={
            "Trading_Day": "Trading Day",
            "Portfolio_Value": "Portfolio Value ($)",
        },
        template="plotly_white",
        render_mode="webgl",
    )

    fig.add_hline(
        y=INITIAL_PORTFOLIO,
        line_dash="dash",
        line_color="black",
        annotation_text="Initial value",
    )

    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
    )
    apply_chart_layout(fig, "Monte Carlo: Sample Portfolio Paths")
    save_chart(fig, "sample_simulation_paths.html")

    # --------------------------------------------------------
    # 7. Interactive chart: percentile fan
    # --------------------------------------------------------
    day_numbers = np.arange(1, HORIZON_DAYS + 1)

    percentiles = {
        "5th percentile": np.quantile(wealth_paths, 0.05, axis=0),
        "25th percentile": np.quantile(wealth_paths, 0.25, axis=0),
        "Median": np.quantile(wealth_paths, 0.50, axis=0),
        "75th percentile": np.quantile(wealth_paths, 0.75, axis=0),
        "95th percentile": np.quantile(wealth_paths, 0.95, axis=0),
    }

    fig = go.Figure()

    # Draw the upper band first, then the lower bound with a fill.
    fig.add_trace(go.Scatter(
        x=day_numbers,
        y=percentiles["95th percentile"],
        mode="lines",
        name="95th percentile",
        line=dict(width=1.5),
    ))

    fig.add_trace(go.Scatter(
        x=day_numbers,
        y=percentiles["5th percentile"],
        mode="lines",
        name="5th percentile",
        fill="tonexty",
        fillcolor="rgba(100, 149, 237, 0.18)",
        line=dict(width=1.5),
    ))

    for name in ("75th percentile", "Median", "25th percentile"):
        fig.add_trace(go.Scatter(
            x=day_numbers,
            y=percentiles[name],
            mode="lines",
            name=name,
            line=dict(width=2 if name == "Median" else 1.3),
        ))

    fig.add_hline(
        y=INITIAL_PORTFOLIO,
        line_dash="dash",
        annotation_text="Initial value",
    )

    fig.update_layout(
        xaxis_title="Trading Day",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
    )
    apply_chart_layout(fig, "Monte Carlo: Portfolio Value Percentile Fan")
    save_chart(fig, "portfolio_percentile_fan.html")

    # --------------------------------------------------------
    # 8. Interactive chart: VaR vs Expected Shortfall
    # --------------------------------------------------------
    risk_plot = metrics.melt(
        id_vars="Confidence_Level",
        value_vars=[
            "VaR_Loss_Amount",
            "Expected_Shortfall_Loss_Amount",
        ],
        var_name="Risk_Measure",
        value_name="Estimated_Loss",
    )

    risk_plot["Confidence_Level"] = risk_plot[
        "Confidence_Level"
    ].map(lambda value: f"{value:.0%}")

    risk_plot["Risk_Measure"] = risk_plot["Risk_Measure"].map({
        "VaR_Loss_Amount": "Value at Risk (VaR)",
        "Expected_Shortfall_Loss_Amount": "Expected Shortfall (ES)",
    })

    fig = px.bar(
        risk_plot,
        x="Confidence_Level",
        y="Estimated_Loss",
        color="Risk_Measure",
        barmode="group",
        text_auto=".2f",
        title="Estimated One-Year Portfolio Loss: VaR vs Expected Shortfall",
        labels={
            "Confidence_Level": "Confidence Level",
            "Estimated_Loss": "Estimated Loss ($)",
            "Risk_Measure": "Risk Measure",
        },
        template="plotly_white",
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "Confidence: %{x}<br>"
            "Risk measure: %{fullData.name}<br>"
            "Estimated loss: $%{y:,.2f}"
            "<extra></extra>"
        ),
    )

    apply_chart_layout(
        fig,
        "Estimated One-Year Portfolio Loss: VaR vs Expected Shortfall",
    )
    save_chart(fig, "var_es_comparison.html")

    # --------------------------------------------------------
    # 9. Interactive chart: terminal return vs outcome
    # --------------------------------------------------------
    outcome_df = pd.DataFrame({
        "Terminal_Value": terminal_values,
        "Terminal_Return_Percent": terminal_returns * 100.0,
        "Profit_Loss": terminal_values - INITIAL_PORTFOLIO,
        "Outcome": np.where(terminal_returns < 0.0, "Loss", "Gain"),
    })

    fig = px.scatter(
        outcome_df,
        x="Terminal_Return_Percent",
        y="Terminal_Value",
        color="Outcome",
        opacity=0.55,
        title="Monte Carlo: Terminal Return vs Portfolio Value",
        labels={
            "Terminal_Return_Percent": "Terminal Return (%)",
            "Terminal_Value": "Terminal Portfolio Value ($)",
            "Profit_Loss": "Profit / Loss ($)",
        },
        hover_data={
            "Profit_Loss": ":,.2f",
            "Terminal_Return_Percent": ":.2f",
            "Terminal_Value": ":,.2f",
        },
        template="plotly_white",
    )

    fig.add_hline(y=INITIAL_PORTFOLIO, line_dash="dash")
    fig.add_vline(x=0, line_dash="dash")

    apply_chart_layout(
        fig,
        "Monte Carlo: Terminal Return vs Portfolio Value",
    )
    save_chart(fig, "terminal_outcomes_scatter.html")

    # --------------------------------------------------------
    # 10. Generate the Markdown summary
    # --------------------------------------------------------
    var95 = metrics.loc[
        np.isclose(metrics["Confidence_Level"], 0.95)
    ].iloc[0]

    var99 = metrics.loc[
        np.isclose(metrics["Confidence_Level"], 0.99)
    ].iloc[0]

    summary_text = f"""# Monte Carlo Portfolio Risk Simulation

## Model setup

- Simulations: {N_SIMULATIONS:,}
- Horizon: {HORIZON_DAYS} trading days
- Initial portfolio value: ${INITIAL_PORTFOLIO:,.2f}
- Assets: {", ".join(assets)}
- Portfolio weights: equal-weighted, rebalanced daily
- Historical return observations: {len(log_returns):,}
- Estimation period: {prices.index.min().date()} to {prices.index.max().date()}
- Random seed: {RANDOM_SEED}

## Simulated results

- Mean terminal value: ${np.mean(terminal_values):,.2f}
- Median terminal value: ${np.median(terminal_values):,.2f}
- 5th percentile terminal value: ${np.quantile(terminal_values, 0.05):,.2f}
- 95th percentile terminal value: ${np.quantile(terminal_values, 0.95):,.2f}
- Probability of ending below the initial value: {np.mean(terminal_returns < 0.0):.2%}
- Worst simulated terminal value: ${np.min(terminal_values):,.2f}
- Best simulated terminal value: ${np.max(terminal_values):,.2f}

## Tail-risk estimates

- 95% VaR loss estimate: ${var95["VaR_Loss_Amount"]:,.2f}
- 95% Expected Shortfall estimate: ${var95["Expected_Shortfall_Loss_Amount"]:,.2f}
- 99% VaR loss estimate: ${var99["VaR_Loss_Amount"]:,.2f}
- 99% Expected Shortfall estimate: ${var99["Expected_Shortfall_Loss_Amount"]:,.2f}

VaR is the negative of the lower-tail terminal-return quantile.
Expected Shortfall is the negative average return among outcomes at or below
that quantile. A negative VaR loss estimate can occur when the modeled lower
return quantile is positive; the code reports the signed quantile-based value
rather than forcing every estimate to be positive.

## Important limitations

This baseline parametric Monte Carlo model estimates a multivariate normal
distribution of daily log returns using historical sample means and covariance.
It converts simulated log returns into simple asset returns and assumes the
portfolio is rebalanced daily to equal weights.

It does not explicitly model fat tails, volatility clustering, regime changes,
liquidity constraints, transaction costs, taxes, or slippage. Historical
parameters may not remain representative of future conditions. Results are
model-based scenarios, not guaranteed forecasts or investment advice.

## Output files

- `simulation_summary.csv`
- `simulated_var_es.csv`
- `terminal_values.csv`
- `sample_simulation_paths.csv`
- `sample_simulated_daily_returns.csv`
- `simulation_configuration.json`
- Interactive charts in `charts/`
"""

    (OUTPUT_DIR / "monte_carlo_summary.md").write_text(
        summary_text,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # 11. Print results
    # --------------------------------------------------------
    print("\nMONTE CARLO SIMULATION COMPLETE")
    print("=" * 55)
    print(f"Simulations:                 {N_SIMULATIONS:,}")
    print(f"Horizon:                     {HORIZON_DAYS} trading days")
    print(f"Initial portfolio:           ${INITIAL_PORTFOLIO:,.2f}")
    print(f"Mean terminal value:         ${np.mean(terminal_values):,.2f}")
    print(f"Median terminal value:       ${np.median(terminal_values):,.2f}")
    print(
        "5th percentile value:        "
        f"${np.quantile(terminal_values, 0.05):,.2f}"
    )
    print(
        "95th percentile value:       "
        f"${np.quantile(terminal_values, 0.95):,.2f}"
    )
    print(
        "Probability of loss:        "
        f"{np.mean(terminal_returns < 0.0):.2%}"
    )
    print(f"95% VaR loss estimate:       ${var95['VaR_Loss_Amount']:,.2f}")
    print(
        "95% Expected Shortfall:     "
        f"${var95['Expected_Shortfall_Loss_Amount']:,.2f}"
    )
    print(f"99% VaR loss estimate:       ${var99['VaR_Loss_Amount']:,.2f}")
    print(
        "99% Expected Shortfall:     "
        f"${var99['Expected_Shortfall_Loss_Amount']:,.2f}"
    )
    print(f"\nAll outputs saved under: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

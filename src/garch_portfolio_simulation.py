
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from arch import arch_model


# ============================================================
# CONFIGURATION
# ============================================================
ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "processed" / "prices_wide.csv"
OUTPUT_DIR = ROOT / "reports" / "garch_comparison"
CHART_DIR = OUTPUT_DIR / "charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

ASSETS = ["AAPL", "AMZN", "GOOGL", "MSFT", "NVDA"]

N_SIMULATIONS = 10_000
HORIZON_DAYS = 252
INITIAL_PORTFOLIO = 10_000.0
TRAIN_FRACTION = 0.80
RANDOM_SEED = 42
CONFIDENCE_LEVELS = (0.95, 0.99)


# ============================================================
# DATA
# ============================================================
def load_returns():
    """Load prices and create aligned daily log returns."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Missing data file: {DATA_FILE}\n"
            "Run the existing data preparation steps first."
        )

    prices = pd.read_csv(
        DATA_FILE,
        index_col=0,
        parse_dates=True,
    )

    if prices.empty:
        raise ValueError("Price dataset is empty.")

    prices = prices.sort_index()
    prices = prices.loc[~prices.index.duplicated(keep="last")]

    missing = [asset for asset in ASSETS if asset not in prices.columns]
    if missing:
        raise ValueError(f"Missing asset columns: {missing}")

    prices = prices[ASSETS].apply(pd.to_numeric, errors="coerce")
    prices = prices.replace([np.inf, -np.inf], np.nan).dropna()

    if (prices <= 0).any().any():
        raise ValueError("All prices must be strictly positive.")

    returns = np.log(prices / prices.shift(1)).dropna()

    if len(returns) < 500:
        raise ValueError(
            "At least 500 daily return observations are required "
            "for this training/holdout comparison."
        )

    if not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Returns contain non-finite values.")

    return returns


# ============================================================
# RISK METRICS
# ============================================================
def calculate_metrics(terminal_values, model_name):
    """Calculate terminal-value and lower-tail risk metrics."""
    terminal_values = np.asarray(terminal_values, dtype=float)

    if (
        terminal_values.ndim != 1
        or len(terminal_values) == 0
        or not np.isfinite(terminal_values).all()
        or (terminal_values < 0).any()
    ):
        raise ValueError("Invalid simulated terminal values.")

    terminal_returns = terminal_values / INITIAL_PORTFOLIO - 1.0

    result = {
        "Model": model_name,
        "Simulation_Count": len(terminal_values),
        "Horizon_Days": HORIZON_DAYS,
        "Initial_Portfolio_Value": INITIAL_PORTFOLIO,
        "Mean_Terminal_Value": float(terminal_values.mean()),
        "Median_Terminal_Value": float(np.median(terminal_values)),
        "Terminal_Value_P05": float(np.quantile(terminal_values, 0.05)),
        "Terminal_Value_P95": float(np.quantile(terminal_values, 0.95)),
        "Probability_Of_Loss_Percent": float(
            np.mean(terminal_returns < 0) * 100
        ),
    }

    for confidence in CONFIDENCE_LEVELS:
        q = float(np.quantile(terminal_returns, 1 - confidence))
        tail = terminal_returns[terminal_returns <= q]

        result[f"VaR_{int(confidence * 100)}_Amount"] = (
            -INITIAL_PORTFOLIO * q
        )
        result[f"ES_{int(confidence * 100)}_Amount"] = (
            -INITIAL_PORTFOLIO * float(tail.mean())
        )

    return result


# ============================================================
# MODEL A: HISTORICAL MULTIVARIATE NORMAL
# ============================================================
def simulate_normal_model(train_returns, rng):
    """Simulate correlated daily log returns using training statistics."""
    mean = train_returns.mean().to_numpy(dtype=float)
    covariance = train_returns.cov().to_numpy(dtype=float)

    covariance = (covariance + covariance.T) / 2
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    covariance = (
        eigenvectors
        @ np.diag(np.clip(eigenvalues, 0, None))
        @ eigenvectors.T
    )
    covariance = (covariance + covariance.T) / 2

    simulated_log_returns = rng.multivariate_normal(
        mean=mean,
        cov=covariance,
        size=(N_SIMULATIONS, HORIZON_DAYS),
        check_valid="raise",
    )

    return portfolio_wealth_paths(simulated_log_returns)


# ============================================================
# MODEL B: GARCH(1,1) WITH JOINT RESIDUAL BOOTSTRAP
# ============================================================
def fit_garch_models(train_returns):
    """
    Fit a GARCH(1,1) model to each asset.

    Returns are multiplied by 100 for numerical scaling. Standardized
    residuals retain their original dates so aligned residual vectors
    can be resampled jointly across assets.
    """
    fitted = {}
    standardized = pd.DataFrame(index=train_returns.index)

    for asset in ASSETS:
        series = train_returns[asset] * 100.0

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = arch_model(
                series,
                mean="Constant",
                vol="GARCH",
                p=1,
                q=1,
                dist="normal",
                rescale=False,
            )
            result = model.fit(disp="off", show_warning=False)

        params = result.params

        required = ["mu", "omega", "alpha[1]", "beta[1]"]
        if any(name not in params.index for name in required):
            raise ValueError(
                f"Unexpected GARCH parameters for {asset}: "
                f"{list(params.index)}"
            )

        omega = float(params["omega"])
        alpha = float(params["alpha[1]"])
        beta = float(params["beta[1]"])

        if omega <= 0 or alpha < 0 or beta < 0:
            raise ValueError(
                f"Invalid GARCH parameters estimated for {asset}."
            )

        if alpha + beta >= 1:
            raise ValueError(
                f"GARCH variance is not covariance-stationary for {asset}: "
                f"alpha + beta = {alpha + beta:.4f}. "
                "Review the model fit before interpreting results."
            )

        conditional_volatility = result.conditional_volatility
        residuals = result.resid / conditional_volatility
        residuals = residuals.replace([np.inf, -np.inf], np.nan)

        standardized[asset] = residuals.reindex(train_returns.index)

        fitted[asset] = {
            "mu": float(params["mu"]),
            "omega": omega,
            "alpha": alpha,
            "beta": beta,
            "last_variance": float(conditional_volatility.iloc[-1] ** 2),
            "convergence_flag": int(result.convergence_flag),
            "log_likelihood": float(result.loglikelihood),
        }

    standardized = standardized.dropna()

    if len(standardized) < 100:
        raise ValueError(
            "Too few aligned standardized residuals for joint bootstrap."
        )

    z = standardized.to_numpy(dtype=float)

    if not np.isfinite(z).all():
        raise ValueError("Standardized residuals contain non-finite values.")

    return fitted, z


def simulate_garch_model(train_returns, rng):
    """
    Simulate asset returns using fitted GARCH(1,1) variance dynamics.

    Joint historical standardized-residual vectors are resampled to
    retain empirical contemporaneous dependence across the five assets.
    Portfolio wealth is calculated using daily equal-weight rebalancing.
    """
    fitted, residual_matrix = fit_garch_models(train_returns)

    n_assets = len(ASSETS)

    mu = np.array([fitted[a]["mu"] for a in ASSETS])
    omega = np.array([fitted[a]["omega"] for a in ASSETS])
    alpha = np.array([fitted[a]["alpha"] for a in ASSETS])
    beta = np.array([fitted[a]["beta"] for a in ASSETS])

    variance = np.tile(
        np.array([fitted[a]["last_variance"] for a in ASSETS]),
        (N_SIMULATIONS, 1),
    )

    simulated_log_returns = np.empty(
        (N_SIMULATIONS, HORIZON_DAYS, n_assets),
        dtype=float,
    )

    for day in range(HORIZON_DAYS):
        # Sample one aligned cross-asset residual vector per simulation.
        row_ids = rng.integers(
            0,
            len(residual_matrix),
            size=N_SIMULATIONS,
        )
        z = residual_matrix[row_ids]

        sigma = np.sqrt(np.maximum(variance, 0.0))

        # GARCH parameters and variance are in percentage units.
        return_percent = mu + sigma * z
        simulated_log_returns[:, day, :] = return_percent / 100.0

        epsilon = return_percent - mu

        variance = (
            omega
            + alpha * np.square(epsilon)
            + beta * variance
        )

        if not np.isfinite(variance).all():
            raise ValueError(
                "GARCH simulation produced non-finite conditional variance."
            )

    return portfolio_wealth_paths(simulated_log_returns), fitted


# ============================================================
# PORTFOLIO VALUATION
# ============================================================
def portfolio_wealth_paths(simulated_log_returns):
    """Convert simulated log returns into daily-rebalanced portfolio wealth."""
    with np.errstate(over="raise", invalid="raise"):
        try:
            simple_returns = np.expm1(simulated_log_returns)
        except FloatingPointError as exc:
            raise ValueError(
                "Simulated returns overflowed; review model assumptions."
            ) from exc

    weights = np.full(len(ASSETS), 1.0 / len(ASSETS))
    portfolio_returns = np.einsum(
        "sda,a->sd",
        simple_returns,
        weights,
    )

    if not np.isfinite(portfolio_returns).all():
        raise ValueError("Portfolio returns contain non-finite values.")

    if (portfolio_returns < -1.0).any():
        raise ValueError(
            "A simulated portfolio daily return fell below -100%."
        )

    with np.errstate(over="raise", invalid="raise"):
        try:
            wealth = INITIAL_PORTFOLIO * np.cumprod(
                1 + portfolio_returns,
                axis=1,
            )
        except FloatingPointError as exc:
            raise ValueError("Portfolio wealth overflowed.") from exc

    if not np.isfinite(wealth).all():
        raise ValueError("Portfolio wealth paths contain non-finite values.")

    return wealth


# ============================================================
# REPORTS AND PLOTLY CHARTS
# ============================================================
def save_chart(fig, filename):
    path = CHART_DIR / filename
    fig.write_html(
        str(path),
        include_plotlyjs=True,
        full_html=True,
    )
    print(f"Saved chart: {path}")


def create_reports(metrics, wealth_by_model):
    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)

    metrics_long = metrics_df.melt(
        id_vars="Model",
        value_vars=[
            "Mean_Terminal_Value",
            "Median_Terminal_Value",
            "Terminal_Value_P05",
            "Terminal_Value_P95",
        ],
        var_name="Statistic",
        value_name="Portfolio_Value",
    )

    fig = px.bar(
        metrics_long,
        x="Statistic",
        y="Portfolio_Value",
        color="Model",
        barmode="group",
        title="Monte Carlo vs GARCH: Terminal Portfolio Value",
        labels={
            "Statistic": "Summary Statistic",
            "Portfolio_Value": "Portfolio Value ($)",
        },
        template="plotly_white",
        hover_data={"Portfolio_Value": ":,.2f"},
    )
    fig.update_layout(hovermode="x unified")
    save_chart(fig, "terminal_value_comparison.html")

    risk_columns = [
        "VaR_95_Amount",
        "ES_95_Amount",
        "VaR_99_Amount",
        "ES_99_Amount",
    ]

    risk_long = metrics_df.melt(
        id_vars="Model",
        value_vars=risk_columns,
        var_name="Risk_Measure",
        value_name="Estimated_Loss",
    )

    fig = px.bar(
        risk_long,
        x="Risk_Measure",
        y="Estimated_Loss",
        color="Model",
        barmode="group",
        title="Model Comparison: Value at Risk and Expected Shortfall",
        labels={
            "Risk_Measure": "Risk Measure",
            "Estimated_Loss": "Quantile-Based Loss Estimate ($)",
        },
        template="plotly_white",
        hover_data={"Estimated_Loss": ":,.2f"},
    )
    fig.update_layout(hovermode="x unified")
    save_chart(fig, "risk_measure_comparison.html")

    fig = go.Figure()

    for model_name, wealth in wealth_by_model.items():
        terminal = wealth[:, -1]
        fig.add_trace(go.Histogram(
            x=terminal,
            name=model_name,
            opacity=0.60,
            nbinsx=80,
            histnorm="probability",
        ))

    fig.add_vline(
        x=INITIAL_PORTFOLIO,
        line_dash="dash",
        annotation_text="Initial investment",
    )

    fig.update_layout(
        title="Terminal Portfolio Value Distributions",
        xaxis_title="Terminal Portfolio Value ($)",
        yaxis_title="Probability per Bin",
        barmode="overlay",
        template="plotly_white",
        hovermode="x",
    )
    save_chart(fig, "terminal_distribution_comparison.html")

    summary_lines = [
        "# Monte Carlo vs GARCH Portfolio Risk Comparison",
        "",
        "## Experimental setup",
        "",
        f"- Assets: {', '.join(ASSETS)}",
        f"- Simulations per model: {N_SIMULATIONS:,}",
        f"- Horizon: {HORIZON_DAYS} trading days",
        f"- Initial portfolio value: ${INITIAL_PORTFOLIO:,.2f}",
        f"- Daily portfolio rebalancing: equal weights",
        f"- Training/holdout split: chronological {TRAIN_FRACTION:.0%}/"
        f"{1 - TRAIN_FRACTION:.0%}",
        "",
        "## Results",
        "",
    ]

    for row in metrics:
        summary_lines.extend([
            f"### {row['Model']}",
            "",
            f"- Mean terminal value: ${row['Mean_Terminal_Value']:,.2f}",
            f"- Median terminal value: ${row['Median_Terminal_Value']:,.2f}",
            f"- Probability of loss: {row['Probability_Of_Loss_Percent']:.2f}%",
            f"- 95% VaR: ${row['VaR_95_Amount']:,.2f}",
            f"- 95% Expected Shortfall: ${row['ES_95_Amount']:,.2f}",
            f"- 99% VaR: ${row['VaR_99_Amount']:,.2f}",
            f"- 99% Expected Shortfall: ${row['ES_99_Amount']:,.2f}",
            "",
        ])

    summary_lines.extend([
        "## Methodology",
        "",
        "The baseline simulates correlated multivariate-normal daily log "
        "returns using the training sample's mean and covariance.",
        "",
        "The GARCH model fits a GARCH(1,1) volatility process to each asset. "
        "Aligned historical standardized residual vectors are resampled "
        "jointly to preserve empirical cross-asset dependence.",
        "",
        "Both models use the same training period, simulation count, horizon, "
        "initial investment, equal portfolio weights, daily rebalancing, "
        "and quantile-based VaR/ES definitions.",
        "",
        "## Limitations",
        "",
        "- This is a model comparison, not proof of predictive superiority.",
        "- GARCH marginal volatility models do not constitute a full "
        "multivariate GARCH model.",
        "- Joint residual bootstrap preserves observed cross-asset shock "
        "vectors but does not model dynamic correlations explicitly.",
        "- Results depend on the estimation period and assumptions.",
        "- Transaction costs, taxes, liquidity, and slippage are excluded.",
        "- A chronological holdout is reserved but is not used in fitting "
        "or in the simulation comparison.",
        "- VaR and Expected Shortfall are model-based estimates, not guarantees.",
        "",
    ])

    (OUTPUT_DIR / "model_comparison_report.md").write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    return metrics_df


# ============================================================
# MAIN
# ============================================================
def main():
    if N_SIMULATIONS <= 0 or HORIZON_DAYS <= 0:
        raise ValueError("Simulation count and horizon must be positive.")

    if INITIAL_PORTFOLIO <= 0:
        raise ValueError("Initial portfolio value must be positive.")

    returns = load_returns()

    split = int(len(returns) * TRAIN_FRACTION)
    train = returns.iloc[:split].copy()
    holdout = returns.iloc[split:].copy()

    if len(train) < 250 or len(holdout) < 50:
        raise ValueError(
            "The training period needs at least 250 rows and the "
            "holdout period at least 50 rows."
        )

    print(f"Training observations: {len(train):,}")
    print(f"Training period: {train.index.min().date()} to "
          f"{train.index.max().date()}")
    print(f"Holdout observations (not used for fitting): {len(holdout):,}")
    print(f"Holdout period: {holdout.index.min().date()} to "
          f"{holdout.index.max().date()}")

    normal_rng = np.random.default_rng(RANDOM_SEED)
    garch_rng = np.random.default_rng(RANDOM_SEED + 1)

    print("\nSimulating multivariate-normal baseline...")
    normal_wealth = simulate_normal_model(train, normal_rng)

    print("Fitting GARCH models and simulating portfolio paths...")
    garch_wealth, fitted = simulate_garch_model(train, garch_rng)

    normal_terminal = normal_wealth[:, -1]
    garch_terminal = garch_wealth[:, -1]

    metrics = [
        calculate_metrics(normal_terminal, "Multivariate Normal"),
        calculate_metrics(garch_terminal, "GARCH(1,1) + Joint Residual Bootstrap"),
    ]

    metrics_df = create_reports(
        metrics,
        {
            "Multivariate Normal": normal_wealth,
            "GARCH(1,1) + Joint Residual Bootstrap": garch_wealth,
        },
    )

    pd.DataFrame([
        {
            "Asset": asset,
            **parameters,
        }
        for asset, parameters in fitted.items()
    ]).to_csv(OUTPUT_DIR / "garch_parameters.csv", index=False)

    metadata = {
        "assets": ASSETS,
        "simulation_count": N_SIMULATIONS,
        "horizon_days": HORIZON_DAYS,
        "initial_portfolio_value": INITIAL_PORTFOLIO,
        "training_fraction": TRAIN_FRACTION,
        "training_start": str(train.index.min().date()),
        "training_end": str(train.index.max().date()),
        "holdout_start": str(holdout.index.min().date()),
        "holdout_end": str(holdout.index.max().date()),
        "holdout_used_for_fitting": False,
        "random_seed_normal": RANDOM_SEED,
        "random_seed_garch": RANDOM_SEED + 1,
        "weights": {asset: 1.0 / len(ASSETS) for asset in ASSETS},
        "garch_distribution": "Normal innovations with joint residual bootstrap",
        "limitations": [
            "Marginal GARCH(1,1) models, not a full multivariate GARCH model.",
            "Joint residual bootstrap retains empirical contemporaneous shocks.",
            "Dynamic cross-asset correlations are not modeled explicitly.",
            "The holdout is reserved but not evaluated in this script.",
            "Transaction costs, taxes, liquidity, and slippage are excluded.",
        ],
    }

    (OUTPUT_DIR / "model_configuration.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("\nMODEL COMPARISON COMPLETE")
    print("=" * 65)
    print(metrics_df.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    print(f"\nReports and charts saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

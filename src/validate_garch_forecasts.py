
from pathlib import Path
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
OUTPUT_DIR = ROOT / "reports" / "garch_validation"
CHART_DIR = OUTPUT_DIR / "charts"

ASSETS = ["AAPL", "AMZN", "GOOGL", "MSFT", "NVDA"]

TRAIN_FRACTION = 0.80
MIN_TRAIN_OBSERVATIONS = 250
MIN_HOLDOUT_OBSERVATIONS = 50
VARIANCE_FLOOR = 1e-10

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATA LOADING
# ============================================================
def load_returns():
    """Load prices and calculate aligned daily log returns."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Price file not found: {DATA_FILE}\n"
            "Run the existing data preparation steps first."
        )

    prices = pd.read_csv(
        DATA_FILE,
        index_col=0,
        parse_dates=True,
    )

    if prices.empty:
        raise ValueError("The price dataset is empty.")

    prices.index = pd.to_datetime(prices.index, errors="coerce")
    prices = prices.loc[prices.index.notna()]
    prices = prices.sort_index()
    prices = prices.loc[
        ~prices.index.duplicated(keep="last")
    ]

    missing_assets = [
        asset for asset in ASSETS
        if asset not in prices.columns
    ]

    if missing_assets:
        raise ValueError(
            f"Missing required asset columns: {missing_assets}"
        )

    prices = prices[ASSETS].apply(
        pd.to_numeric,
        errors="coerce",
    )

    prices = prices.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    if prices.empty:
        raise ValueError(
            "No complete price observations remain after cleaning."
        )

    if (prices <= 0).any().any():
        raise ValueError("All asset prices must be positive.")

    returns = np.log(prices / prices.shift(1)).dropna()

    if len(returns) < 500:
        raise ValueError(
            "At least 500 daily return observations are required."
        )

    if not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Returns contain non-finite values.")

    return returns


# ============================================================
# CHRONOLOGICAL TRAIN / HOLDOUT SPLIT
# ============================================================
def split_returns(returns):
    """Split returns chronologically without shuffling."""

    split_index = int(len(returns) * TRAIN_FRACTION)

    train = returns.iloc[:split_index].copy()
    holdout = returns.iloc[split_index:].copy()

    if len(train) < MIN_TRAIN_OBSERVATIONS:
        raise ValueError(
            "The training period contains too few observations."
        )

    if len(holdout) < MIN_HOLDOUT_OBSERVATIONS:
        raise ValueError(
            "The holdout period contains too few observations."
        )

    if train.index.max() >= holdout.index.min():
        raise ValueError(
            "Training and holdout periods overlap."
        )

    return train, holdout


# ============================================================
# QLIKE FORECAST LOSS
# ============================================================
def qlike_loss(realized_variance, forecast_variance):
    """
    Calculate mean QLIKE loss.

    QLIKE = mean(log(h_t) + y_t / h_t)

    h_t = forecast variance
    y_t = realized squared-return proxy

    Lower scores indicate better forecasts when the target and
    evaluation sample are identical.
    """

    realized = np.asarray(
        realized_variance,
        dtype=float,
    )

    forecast = np.asarray(
        forecast_variance,
        dtype=float,
    )

    if realized.shape != forecast.shape:
        raise ValueError(
            "Realized and forecast arrays must have equal shapes."
        )

    if realized.size == 0:
        raise ValueError(
            "At least one observation is required."
        )

    if (
        not np.isfinite(realized).all()
        or not np.isfinite(forecast).all()
    ):
        raise ValueError(
            "QLIKE inputs must contain only finite values."
        )

    if (realized < 0).any():
        raise ValueError(
            "Realized variance proxies cannot be negative."
        )

    if (forecast <= 0).any():
        raise ValueError(
            "Forecast variances must be strictly positive."
        )

    losses = np.log(forecast) + realized / forecast

    if not np.isfinite(losses).all():
        raise ValueError(
            "QLIKE calculation produced non-finite values."
        )

    return float(np.mean(losses))


# ============================================================
# GARCH(1,1) FORECAST
# ============================================================
def forecast_garch(train_series, holdout_series):
    """
    Fit GARCH(1,1) using training observations only.

    Generate sequential one-step-ahead variance forecasts.
    Each holdout return is used only after its forecast has been made.

    Returns:
        forecast_variance: variance forecasts in percentage-squared units
        parameters: fitted model parameters and diagnostics
    """

    train_pct = train_series.astype(float) * 100.0
    holdout_pct = holdout_series.astype(float) * 100.0

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        model = arch_model(
            train_pct,
            mean="Constant",
            vol="GARCH",
            p=1,
            q=1,
            dist="normal",
            rescale=False,
        )

        result = model.fit(
            disp="off",
            show_warning=False,
        )

    if int(result.convergence_flag) != 0:
        raise ValueError(
            f"GARCH did not converge for {train_series.name}. "
            f"Convergence flag: {result.convergence_flag}"
        )

    params = result.params

    required_parameters = [
        "mu",
        "omega",
        "alpha[1]",
        "beta[1]",
    ]

    missing_parameters = [
        name for name in required_parameters
        if name not in params.index
    ]

    if missing_parameters:
        raise ValueError(
            f"Missing GARCH parameters for {train_series.name}: "
            f"{missing_parameters}"
        )

    mu = float(params["mu"])
    omega = float(params["omega"])
    alpha = float(params["alpha[1]"])
    beta = float(params["beta[1]"])

    if omega <= 0 or alpha < 0 or beta < 0:
        raise ValueError(
            f"Invalid GARCH parameters for {train_series.name}."
        )

    if alpha + beta >= 1:
        raise ValueError(
            f"GARCH variance is not stationary for {train_series.name}: "
            f"alpha + beta = {alpha + beta:.6f}"
        )

    # Last training-period residual and variance.
    last_residual = float(result.resid.iloc[-1])

    last_variance = float(
        result.conditional_volatility.iloc[-1] ** 2
    )

    forecasts = []

    for actual_return in holdout_pct.to_numpy(dtype=float):

        # Forecast the next observation's variance before seeing
        # that observation's return.
        next_variance = (
            omega
            + alpha * last_residual**2
            + beta * last_variance
        )

        next_variance = max(
            float(next_variance),
            VARIANCE_FLOOR,
        )

        forecasts.append(next_variance)

        # After recording the forecast, use the observed return
        # to update the variance state for the following day.
        current_residual = float(actual_return - mu)

        last_residual = current_residual
        last_variance = next_variance

    forecast_variance = np.asarray(
        forecasts,
        dtype=float,
    )

    if not np.isfinite(forecast_variance).all():
        raise ValueError(
            f"Non-finite GARCH forecasts for {train_series.name}."
        )

    parameter_record = {
        "Asset": train_series.name,
        "Mean_Mu_Percent": mu,
        "Omega": omega,
        "Alpha_1": alpha,
        "Beta_1": beta,
        "Alpha_Plus_Beta": alpha + beta,
        "Log_Likelihood": float(result.loglikelihood),
        "Convergence_Flag": int(result.convergence_flag),
        "Training_Observations": len(train_series),
        "Holdout_Observations": len(holdout_series),
    }

    return forecast_variance, parameter_record


# ============================================================
# HISTORICAL VARIANCE BASELINE
# ============================================================
def forecast_historical_variance(train_series, holdout_series):
    """
    Generate an expanding historical-variance forecast.

    The training-sample mean remains fixed throughout the holdout.
    The variance estimate at each date uses only prior observations.
    """

    train_pct = (
        train_series.astype(float).to_numpy() * 100.0
    )

    holdout_pct = (
        holdout_series.astype(float).to_numpy() * 100.0
    )

    training_mean = float(np.mean(train_pct))

    # Store returns centered using the training-sample mean.
    history = (train_pct - training_mean).tolist()

    forecasts = []

    for actual_return in holdout_pct:

        if len(history) < 2:
            raise ValueError(
                "At least two past observations are needed."
            )

        # Sample variance based only on information available
        # before observing the current holdout return.
        forecast_variance = float(
            np.var(np.asarray(history), ddof=1)
        )

        forecast_variance = max(
            forecast_variance,
            VARIANCE_FLOOR,
        )

        forecasts.append(forecast_variance)

        # Update history after this date's forecast is recorded.
        history.append(
            float(actual_return - training_mean)
        )

    forecast_variance = np.asarray(
        forecasts,
        dtype=float,
    )

    if not np.isfinite(forecast_variance).all():
        raise ValueError(
            f"Non-finite historical forecasts for {train_series.name}."
        )

    return forecast_variance


# ============================================================
# PLOTLY CHART SAVING
# ============================================================
def save_chart(fig, filename):
    """Save an interactive standalone HTML chart."""

    output_path = CHART_DIR / filename

    fig.write_html(
        str(output_path),
        include_plotlyjs=True,
        full_html=True,
    )

    print(f"Saved chart: {output_path}")


# ============================================================
# MODEL VALIDATION
# ============================================================
def build_validation_report(train, holdout):
    """Forecast holdout volatility, compare models, and save reports."""

    forecast_records = []
    score_records = []
    parameter_records = []

    for asset in ASSETS:

        print(f"Fitting and validating {asset}...")

        train_series = train[asset]
        holdout_series = holdout[asset]

        # Fit GARCH on training data and generate holdout forecasts.
        garch_variance, parameters = forecast_garch(
            train_series,
            holdout_series,
        )

        parameter_records.append(parameters)

        # Generate historical benchmark forecasts.
        historical_variance = forecast_historical_variance(
            train_series,
            holdout_series,
        )

        # Use the same target for both models: squared returns
        # demeaned by the training-sample mean.
        training_mean_pct = float(
            train_series.mean() * 100.0
        )

        holdout_returns_pct = (
            holdout_series.to_numpy(dtype=float) * 100.0
        )

        realized_proxy = (
            holdout_returns_pct - training_mean_pct
        ) ** 2

        # QLIKE comparison.
        garch_score = qlike_loss(
            realized_proxy,
            garch_variance,
        )

        historical_score = qlike_loss(
            realized_proxy,
            historical_variance,
        )

        score_records.extend([
            {
                "Asset": asset,
                "Model": "GARCH(1,1)",
                "Holdout_Observations": len(holdout),
                "QLIKE_Mean": garch_score,
            },
            {
                "Asset": asset,
                "Model": "Expanding Historical Variance",
                "Holdout_Observations": len(holdout),
                "QLIKE_Mean": historical_score,
            },
        ])

        model_forecasts = [
            (
                "GARCH(1,1)",
                garch_variance,
            ),
            (
                "Expanding Historical Variance",
                historical_variance,
            ),
        ]

        for model_name, variance in model_forecasts:

            volatility = np.sqrt(variance)

            for date, forecast_var, forecast_vol, realized in zip(
                holdout.index,
                variance,
                volatility,
                realized_proxy,
            ):
                forecast_records.append({
                    "Asset": asset,
                    "Date": date,
                    "Model": model_name,
                    "Forecast_Variance_Percent2": float(
                        forecast_var
                    ),
                    "Forecast_Daily_Volatility_Percent": float(
                        forecast_vol
                    ),
                    "Realized_Squared_Return_Percent2": float(
                        realized
                    ),
                })

    forecasts_df = pd.DataFrame(forecast_records)
    scores_df = pd.DataFrame(score_records)
    parameters_df = pd.DataFrame(parameter_records)

    # --------------------------------------------------------
    # Save output tables
    # --------------------------------------------------------
    forecasts_df.to_csv(
        OUTPUT_DIR / "holdout_volatility_forecasts.csv",
        index=False,
    )

    scores_df.to_csv(
        OUTPUT_DIR / "qlike_scores.csv",
        index=False,
    )

    parameters_df.to_csv(
        OUTPUT_DIR / "garch_validation_parameters.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Chart 1: QLIKE model comparison
    # --------------------------------------------------------
    fig = px.bar(
        scores_df,
        x="Asset",
        y="QLIKE_Mean",
        color="Model",
        barmode="group",
        title="Out-of-Sample Volatility Forecast Accuracy",
        labels={
            "Asset": "Asset",
            "QLIKE_Mean": "Mean QLIKE Loss (lower is better)",
            "Model": "Forecast Model",
        },
        template="plotly_white",
        hover_data={
            "QLIKE_Mean": ":.5f",
            "Holdout_Observations": True,
        },
    )

    fig.update_layout(
        hovermode="x unified",
        legend_title_text="Forecast Model",
    )

    save_chart(
        fig,
        "qlike_model_comparison.html",
    )

    # --------------------------------------------------------
    # Chart 2: Forecast volatility over time
    # --------------------------------------------------------
    fig = px.line(
        forecasts_df,
        x="Date",
        y="Forecast_Daily_Volatility_Percent",
        color="Model",
        facet_row="Asset",
        title="Holdout Daily Volatility Forecasts by Asset",
        labels={
            "Date": "Date",
            "Forecast_Daily_Volatility_Percent":
                "Forecast Daily Volatility (%)",
            "Model": "Forecast Model",
        },
        template="plotly_white",
    )

    fig.update_layout(
        hovermode="x unified",
        height=1200,
    )

    fig.for_each_annotation(
        lambda annotation: annotation.update(
            text=annotation.text.replace("Asset=", "")
        )
    )

    save_chart(
        fig,
        "holdout_volatility_forecasts.html",
    )

    # --------------------------------------------------------
    # Chart 3: NVDA variance forecasts vs realized proxy
    # --------------------------------------------------------
    asset_to_plot = "NVDA"

    plot_df = forecasts_df[
        forecasts_df["Asset"] == asset_to_plot
    ]

    fig = go.Figure()

    for model_name in [
        "GARCH(1,1)",
        "Expanding Historical Variance",
    ]:
        subset = plot_df[
            plot_df["Model"] == model_name
        ]

        fig.add_trace(
            go.Scatter(
                x=subset["Date"],
                y=subset["Forecast_Variance_Percent2"],
                mode="lines",
                name=f"{model_name} forecast",
                hovertemplate=(
                    "Date: %{x|%Y-%m-%d}<br>"
                    "Forecast variance: %{y:.4f}<extra></extra>"
                ),
            )
        )

    realized_df = plot_df[
        plot_df["Model"] == "GARCH(1,1)"
    ]

    fig.add_trace(
        go.Scatter(
            x=realized_df["Date"],
            y=realized_df[
                "Realized_Squared_Return_Percent2"
            ],
            mode="lines",
            name="Realized squared-return proxy",
            opacity=0.55,
            hovertemplate=(
                "Date: %{x|%Y-%m-%d}<br>"
                "Squared-return proxy: %{y:.4f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=(
            f"{asset_to_plot}: Forecast Variance "
            "vs Realized Squared-Return Proxy"
        ),
        xaxis_title="Date",
        yaxis_title=(
            "Variance (percentage-return squared)"
        ),
        template="plotly_white",
        hovermode="x unified",
    )

    save_chart(
        fig,
        "nvda_variance_forecast_vs_realized.html",
    )

    # --------------------------------------------------------
    # Chart 4: Relative QLIKE improvement
    # --------------------------------------------------------
    score_pivot = scores_df.pivot(
        index="Asset",
        columns="Model",
        values="QLIKE_Mean",
    )

    baseline_column = "Expanding Historical Variance"
    garch_column = "GARCH(1,1)"

    baseline_scores = score_pivot[baseline_column]
    garch_scores = score_pivot[garch_column]

    improvement = (
        (baseline_scores - garch_scores)
        / baseline_scores.abs().clip(lower=VARIANCE_FLOOR)
    ) * 100.0

    improvement_df = pd.DataFrame({
        "Asset": improvement.index,
        "GARCH_QLIKE_Improvement_Percent":
            improvement.to_numpy(),
    })

    improvement_df.to_csv(
        OUTPUT_DIR / "qlike_improvement.csv",
        index=False,
    )

    fig = px.bar(
        improvement_df,
        x="Asset",
        y="GARCH_QLIKE_Improvement_Percent",
        title="GARCH QLIKE Improvement vs Historical Baseline",
        labels={
            "Asset": "Asset",
            "GARCH_QLIKE_Improvement_Percent":
                "QLIKE improvement (%)",
        },
        template="plotly_white",
        hover_data={
            "GARCH_QLIKE_Improvement_Percent": ":.2f",
        },
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        annotation_text="No improvement",
    )

    fig.update_layout(
        hovermode="x",
    )

    save_chart(
        fig,
        "qlike_improvement.html",
    )

    # --------------------------------------------------------
    # Markdown report
    # --------------------------------------------------------
    score_table = scores_df.to_markdown(
        index=False,
        floatfmt=".5f",
    )

    report_lines = [
        "# GARCH Out-of-Sample Volatility Validation",
        "",
        "## Evaluation design",
        "",
        f"- Training observations: {len(train):,}",
        (
            f"- Training period: {train.index.min().date()} "
            f"to {train.index.max().date()}"
        ),
        f"- Holdout observations: {len(holdout):,}",
        (
            f"- Holdout period: {holdout.index.min().date()} "
            f"to {holdout.index.max().date()}"
        ),
        f"- Assets evaluated: {', '.join(ASSETS)}",
        "- GARCH parameters are estimated using training data only.",
        "- Holdout returns are used only after each daily forecast.",
        "- The benchmark uses expanding historical sample variance.",
        (
            "- Both models are evaluated against squared returns "
            "demeaned by the training-sample mean."
        ),
        "",
        "## QLIKE results",
        "",
        score_table,
        "",
        "Lower QLIKE indicates a better score for the same target "
        "and evaluation sample.",
        "",
        "## Interpretation",
        "",
        (
            "A positive QLIKE improvement means GARCH had a lower "
            "mean QLIKE loss than the historical baseline. A negative "
            "value means the historical baseline performed better."
        ),
        "",
        (
            "Squared returns are noisy proxies for latent variance. "
            "The comparison evaluates forecasts, not future investment "
            "returns or profitability."
        ),
        "",
        "## Limitations",
        "",
        "- The model uses a constant conditional mean.",
        "- GARCH assumes a GARCH(1,1) conditional variance process.",
        "- The historical baseline is an expanding-variance benchmark.",
        "- Results depend on the chosen training and holdout periods.",
        "- Forecast comparisons do not guarantee future performance.",
        "",
    ]

    report_path = OUTPUT_DIR / "garch_validation_report.md"

    report_path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print("\nVALIDATION COMPLETE")
    print("=" * 70)

    print("\nQLIKE MODEL COMPARISON")
    print(
        scores_df.to_string(
            index=False,
            float_format=lambda value: f"{value:.5f}",
        )
    )

    print("\nGARCH PARAMETERS")
    print(
        parameters_df.to_string(
            index=False,
            float_format=lambda value: f"{value:.5f}",
        )
    )

    print(f"\nMarkdown report: {report_path}")
    print(f"All reports and charts: {OUTPUT_DIR}")


# ============================================================
# MAIN
# ============================================================
def main():
    print("Loading price data...")

    returns = load_returns()
    train, holdout = split_returns(returns)

    print(f"Total return observations: {len(returns):,}")
    print(f"Training observations: {len(train):,}")
    print(
        f"Training period: {train.index.min().date()} "
        f"to {train.index.max().date()}"
    )
    print(f"Holdout observations: {len(holdout):,}")
    print(
        f"Holdout period: {holdout.index.min().date()} "
        f"to {holdout.index.max().date()}"
    )

    print(
        "\nStarting out-of-sample volatility forecast validation..."
    )

    build_validation_report(train, holdout)


if __name__ == "__main__":
    main()

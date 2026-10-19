from pathlib import Path
import html
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MC = ROOT / "reports" / "monte_carlo"
CHARTS = MC / "charts"
DOCS = ROOT / "docs"

DOCS.mkdir(parents=True, exist_ok=True)


def require_file(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}\n"
            "Run src/monte_carlo_simulation.py first."
        )


def money(value):
    return f"${value:,.2f}"


def pct(value):
    return f"{value:.2f}%"


def read_inputs():
    summary_path = MC / "simulation_summary.csv"
    var_path = MC / "simulated_var_es.csv"
    terminal_path = MC / "terminal_values.csv"
    config_path = MC / "simulation_configuration.json"

    for path in (summary_path, var_path, terminal_path, config_path):
        require_file(path)

    summary = pd.read_csv(summary_path).iloc[0].to_dict()
    risk = pd.read_csv(var_path)
    terminal = pd.read_csv(terminal_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))

    terminal_values = terminal["Terminal_Value"].astype(float)
    terminal_returns = terminal["Terminal_Return_Percent"].astype(float) / 100

    return summary, risk, terminal, terminal_values, terminal_returns, config


def metric_card(label, value, subtitle):
    return f"""
    <article class="metric">
      <div class="metric-label">{html.escape(label)}</div>
      <div class="metric-value">{html.escape(str(value))}</div>
      <div class="metric-subtitle">{html.escape(subtitle)}</div>
    </article>
    """


def generate_dashboard(summary, risk, terminal_values, terminal_returns, config):
    charts = [
        (
            "Terminal Value Distribution",
            "terminal_value_distribution.html",
            "Distribution of simulated portfolio values at the end of the horizon."
        ),
        (
            "Simulated Portfolio Paths",
            "sample_simulation_paths.html",
            "A sample of simulated daily portfolio-value paths."
        ),
        (
            "Portfolio Percentile Fan",
            "portfolio_percentile_fan.html",
            "Daily 5th, 25th, median, 75th, and 95th percentile portfolio values."
        ),
        (
            "Value at Risk vs Expected Shortfall",
            "var_es_comparison.html",
            "Compares quantile-based tail loss with average loss in the lower tail."
        ),
        (
            "Terminal Return vs Portfolio Value",
            "terminal_outcomes_scatter.html",
            "Each point represents a simulated terminal outcome."
        ),
    ]

    for _, filename, _ in charts:
        require_file(CHARTS / filename)

    risk95 = risk.loc[np.isclose(risk["Confidence_Level"], 0.95)].iloc[0]
    risk99 = risk.loc[np.isclose(risk["Confidence_Level"], 0.99)].iloc[0]

    initial = float(summary["Initial_Portfolio_Value"])
    median = float(summary["Median_Terminal_Value"])
    mean = float(summary["Mean_Terminal_Value"])
    p5 = float(summary["5th_Percentile_Terminal_Value"])
    p95 = float(summary["95th_Percentile_Terminal_Value"])
    loss_probability = float(summary["Probability_Of_Loss_Percent"])

    chart_html = ""
    for title, filename, description in charts:
        chart_html += f"""
        <section class="chart-card">
          <div class="chart-heading">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(description)}</p>
          </div>
          <iframe
            src="charts/{html.escape(filename)}"
            title="{html.escape(title)}"
            loading="lazy">
          </iframe>
        </section>
        """

    dashboard = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monte Carlo Portfolio Risk Dashboard</title>
<style>
:root {{
  --bg: #f3f6fb;
  --panel: #ffffff;
  --ink: #17243a;
  --muted: #65738a;
  --line: #e0e7f0;
  --accent: #2563eb;
  --accent-soft: #eaf1ff;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: Inter, Segoe UI, Arial, sans-serif;
  background: var(--bg);
  color: var(--ink);
}}
header {{
  padding: 38px max(22px, calc((100% - 1400px) / 2));
  color: white;
  background: linear-gradient(120deg, #14233f, #244d80);
}}
header .eyebrow {{
  text-transform: uppercase;
  letter-spacing: 2px;
  font-size: 12px;
  opacity: .8;
}}
header h1 {{ margin: 10px 0; font-size: clamp(28px, 4vw, 42px); }}
header p {{ max-width: 850px; line-height: 1.7; color: #e1eaf7; }}
main {{ max-width: 1400px; margin: auto; padding: 26px 20px 50px; }}
.section-title {{ margin: 30px 0 14px; }}
.section-title p {{ color: var(--muted); line-height: 1.6; }}
.metrics {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(205px, 1fr));
  gap: 14px;
}}
.metric, .chart-card, .explain {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 15px;
  box-shadow: 0 5px 20px rgba(30, 50, 80, .045);
}}
.metric {{ padding: 20px; }}
.metric-label {{ color: var(--muted); font-size: 13px; }}
.metric-value {{ font-size: clamp(23px, 2.6vw, 32px); font-weight: 750; margin: 12px 0 8px; }}
.metric-subtitle {{ color: var(--muted); font-size: 12px; line-height: 1.5; }}
.charts {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 570px), 1fr));
  gap: 18px;
}}
.chart-card {{ overflow: hidden; }}
.chart-heading {{ padding: 18px 20px 4px; }}
.chart-heading h2 {{ font-size: 19px; margin: 0 0 7px; }}
.chart-heading p {{ font-size: 13px; color: var(--muted); line-height: 1.5; }}
iframe {{ width: 100%; height: 440px; border: 0; display: block; background: white; }}
.explain {{ padding: 22px; margin: 18px 0; line-height: 1.7; }}
.explain h2 {{ margin-top: 0; }}
.grid-two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }}
a {{ color: var(--accent); }}
.notice {{ border-left: 4px solid var(--accent); background: var(--accent-soft); padding: 14px 17px; border-radius: 8px; }}
footer {{ color: var(--muted); padding: 25px 0 0; font-size: 12px; }}
@media (max-width: 650px) {{
  main {{ padding: 16px 12px 30px; }}
  iframe {{ height: 380px; }}
}}
</style>
</head>
<body>
<header>
  <div class="eyebrow">Quantitative Finance · Risk Analytics</div>
  <h1>Monte Carlo Portfolio Risk Dashboard</h1>
  <p>
    A scenario-based analysis of a five-stock, equal-weighted portfolio.
    Historical daily log-return means and covariance are used to simulate
    correlated asset returns and estimate one-year portfolio outcomes and tail risk.
  </p>
</header>
<main>
  <div class="section-title">
    <h2>Simulation at a glance</h2>
    <p>
      {int(summary["Simulation_Count"]):,} simulations ·
      {int(summary["Horizon_Trading_Days"])} trading days ·
      Historical sample: {html.escape(str(summary["Historical_Start_Date"]))}
      to {html.escape(str(summary["Historical_End_Date"]))}
    </p>
  </div>
  <section class="metrics">
    {metric_card("Initial portfolio", money(initial), "Starting hypothetical investment")}
    {metric_card("Mean terminal value", money(mean), "Arithmetic average of simulated terminal values")}
    {metric_card("Median terminal value", money(median), "50th percentile simulated outcome")}
    {metric_card("5th percentile value", money(p5), "5% of modeled outcomes are at or below this value")}
    {metric_card("95th percentile value", money(p95), "95% of modeled outcomes are at or below this value")}
    {metric_card("Probability of loss", pct(loss_probability), "Share of paths ending below the initial investment")}
    {metric_card("95% VaR loss estimate", money(risk95["VaR_Loss_Amount"]), "Lower-tail quantile converted to a loss amount")}
    {metric_card("95% Expected Shortfall", money(risk95["Expected_Shortfall_Loss_Amount"]), "Average loss among outcomes in the 5% lower tail")}
    {metric_card("99% VaR loss estimate", money(risk99["VaR_Loss_Amount"]), "More extreme lower-tail quantile")}
    {metric_card("99% Expected Shortfall", money(risk99["Expected_Shortfall_Loss_Amount"]), "Average loss among outcomes in the 1% lower tail")}
  </section>

  <div class="section-title">
    <h2>Interactive visual analysis</h2>
    <p>Hover over chart points and bars for values; use Plotly tools to zoom, pan, and reset views.</p>
  </div>
  <section class="charts">{chart_html}</section>

  <section class="explain">
    <h2>How to interpret the dashboard</h2>
    <div class="grid-two">
      <div>
        <h3>Terminal value distribution</h3>
        <p>Shows how frequently simulated paths finish at different portfolio values. A wide distribution indicates substantial uncertainty. The initial investment line helps distinguish gains from losses.</p>
      </div>
      <div>
        <h3>Simulated portfolio paths</h3>
        <p>Shows a sample of individual possible journeys, not a prediction of the actual market path. The paths diverge because daily returns are randomly sampled from the estimated joint distribution.</p>
      </div>
      <div>
        <h3>Percentile fan</h3>
        <p>The 5th percentile is a modeled lower-tail outcome, the median is the central outcome, and the 95th percentile is an upper-tail outcome. The percentile lines are not confidence intervals for a single realized future path.</p>
      </div>
      <div>
        <h3>VaR and Expected Shortfall</h3>
        <p>VaR identifies a quantile of the loss distribution. Expected Shortfall averages losses in the tail beyond that quantile. ES helps describe the severity of tail outcomes that VaR alone does not summarize.</p>
      </div>
      <div>
        <h3>Terminal outcome scatter</h3>
        <p>Each dot represents one simulated outcome. Outcomes below the initial portfolio value are losses; outcomes above it are gains. This chart is useful for seeing the spread and concentration of results.</p>
      </div>
      <div>
        <h3>Equal-weighted portfolio</h3>
        <p>The model weights the five stocks equally and rebalances daily. It does not include the S&amp;P 500 in the portfolio; the benchmark is not an investable component in this simulation.</p>
      </div>
    </div>
  </section>

  <section class="explain">
    <h2>Model assumptions and cautions</h2>
    <p>
      Daily log returns are simulated from a multivariate normal distribution
      estimated using historical sample means and covariance. Correlation is
      represented through the covariance matrix. Simulated log returns are
      converted to simple returns, and daily portfolio returns are calculated
      as the weighted sum of constituent simple returns.
    </p>
    <div class="notice">
      These results are conditional model estimates, not guaranteed forecasts.
      A normal-return model may understate fat tails, volatility clustering,
      abrupt regime changes, and extreme market events. Historical estimates
      are uncertain, and transaction costs, taxes, liquidity, and slippage are
      excluded.
    </div>
  </section>

  <section class="explain">
    <h2>Repository outputs</h2>
    <ul>
      <li><code>simulation_summary.csv</code> — headline simulation statistics.</li>
      <li><code>simulated_var_es.csv</code> — 95% and 99% tail-risk metrics.</li>
      <li><code>terminal_values.csv</code> — terminal result for every simulation.</li>
      <li><code>sample_simulation_paths.csv</code> — saved sample of portfolio paths.</li>
      <li><code>monte_carlo_analysis_report.md</code> — detailed narrative report.</li>
      <li><code>../historical_analysis_summary.md</code> — historical analysis summary.</li>
    </ul>
    <p><a href="monte_carlo_analysis_report.md">Read the detailed analysis report</a></p>
    <p><a href="../../docs/MONTE_CARLO_METHODOLOGY.md">Read the model methodology</a></p>
    <p><a href="../../docs/REFERENCES.md">Read the research references</a></p>
  </section>
  <footer>
    Generated from the project's saved Monte Carlo outputs. Model assumptions and estimation period should be reviewed before using these figures in decisions.
  </footer>
</main>
</body>
</html>
"""

    (MC / "monte_carlo_dashboard.html").write_text(
        dashboard, encoding="utf-8"
    )


def generate_analysis_report(summary, risk, terminal, terminal_values, terminal_returns, config):
    initial = float(summary["Initial_Portfolio_Value"])
    mean = float(terminal_values.mean())
    median = float(terminal_values.median())
    std_value = float(terminal_values.std(ddof=1))
    p1, p5, p25, p75, p95, p99 = np.quantile(
        terminal_values, [0.01, 0.05, 0.25, 0.75, 0.95, 0.99]
    )
    loss_prob = float((terminal_values < initial).mean() * 100)
    gain_prob = float((terminal_values > initial).mean() * 100)
    mean_return = float(terminal_returns.mean() * 100)
    median_return = float(terminal_returns.median() * 100)

    r95 = risk.loc[np.isclose(risk["Confidence_Level"], 0.95)].iloc[0]
    r99 = risk.loc[np.isclose(risk["Confidence_Level"], 0.99)].iloc[0]

    report = f"""# Monte Carlo Portfolio Risk Simulation — Analysis Report

## 1. Executive summary

This project uses Monte Carlo simulation to explore a range of possible one-year
outcomes for a hypothetical equal-weighted portfolio of five US technology
stocks: {summary["Assets"]}. It generates **{int(summary["Simulation_Count"]):,}
simulated paths**, each spanning **{int(summary["Horizon_Trading_Days"])} trading days**,
starting from **{money(initial)}**.

The model estimates a mean terminal value of **{money(mean)}** and a median
terminal value of **{money(median)}**. The modeled probability of ending below
the initial investment is **{loss_prob:.2f}%**. The 95% VaR loss estimate is
**{money(r95["VaR_Loss_Amount"])}**, while the 95% Expected Shortfall estimate is
**{money(r95["Expected_Shortfall_Loss_Amount"])}**.

These are the outputs of the configured model, not predictions or guaranteed
investment outcomes. The numerical values depend on the sample period, return
distribution assumptions, portfolio weights, and random seed.

## 2. What was analysed

### Historical input data

- Historical start date: {summary["Historical_Start_Date"]}
- Historical end date: {summary["Historical_End_Date"]}
- Daily return observations: {int(summary["Historical_Return_Observations"]):,}
- Assets: {summary["Assets"]}
- Starting portfolio value: {money(initial)}
- Portfolio weights: equal weights across five stocks
- Rebalancing: daily
- Simulation seed: {summary["Random_Seed"]}

The price series is converted to daily log returns:

\\[
r_{{i,t}} = \\ln\\left(\\frac{{P_{{i,t}}}}{{P_{{i,t-1}}}}\\right)
\\]

For each asset, the sample mean and the joint covariance matrix are estimated
from historical daily log returns. The covariance matrix captures both each
asset's variability and the estimated co-movement between assets.

### Correlated simulation

For each simulated day, the model draws a vector of asset log returns from a
multivariate normal distribution:

\\[
\\mathbf{{r}}_t \\sim \\mathcal{{N}}(\\boldsymbol{{\\mu}}, \\boldsymbol{{\\Sigma}})
\\]

The simulated log returns are converted to simple returns:

\\[
R_{{i,t}} = e^{{r_{{i,t}}}} - 1
\\]

With equal weights \\(w_i = 1/5\\), the portfolio's daily return is:

\\[
R_{{p,t}} = \\sum_{{i=1}}^5 w_i R_{{i,t}}
\\]

The portfolio is rebalanced to equal weights each simulated day. Portfolio
value is compounded through the horizon:

\\[
V_T = V_0 \\prod_{{t=1}}^T (1+R_{{p,t}})
\\]

The simulation uses {int(summary["Simulation_Count"]):,} paths, each with
{int(summary["Horizon_Trading_Days"])} trading days.

## 3. Main results

| Metric | Result | Interpretation |
|---|---:|---|
| Initial portfolio value | {money(initial)} | Starting hypothetical capital |
| Mean terminal value | {money(mean)} | Average terminal value across simulations |
| Median terminal value | {money(median)} | Middle simulated outcome |
| Standard deviation of terminal values | {money(std_value)} | Spread of terminal dollar values |
| 1st percentile terminal value | {money(p1)} | Very low modeled outcome |
| 5th percentile terminal value | {money(p5)} | Lower-tail outcome |
| 25th percentile terminal value | {money(p25)} | Lower quartile |
| 75th percentile terminal value | {money(p75)} | Upper quartile |
| 95th percentile terminal value | {money(p95)} | Upper-tail outcome |
| 99th percentile terminal value | {money(p99)} | Very high modeled outcome |
| Mean terminal return | {mean_return:.2f}% | Average simulated return |
| Median terminal return | {median_return:.2f}% | Median simulated return |
| Probability of ending below initial value | {loss_prob:.2f}% | Fraction of paths with a loss |
| Probability of ending above initial value | {gain_prob:.2f}% | Fraction of paths with a gain |

The percentile values describe the distribution of terminal outcomes. For example,
the 5th percentile means approximately 5% of modeled outcomes are at or below that
value under the model assumptions. It is not a guarantee that future value will
remain above that threshold.

## 4. Value at Risk and Expected Shortfall

| Confidence | VaR loss estimate | Expected Shortfall loss estimate | Tail count |
|---|---:|---:|---:|
| 95% | {money(r95["VaR_Loss_Amount"])} | {money(r95["Expected_Shortfall_Loss_Amount"])} | {int(r95["Tail_Simulation_Count"]):,} |
| 99% | {money(r99["VaR_Loss_Amount"])} | {money(r99["Expected_Shortfall_Loss_Amount"])} | {int(r99["Tail_Simulation_Count"]):,} |

For terminal return \\(R_T = V_T/V_0 - 1\\), the lower-tail quantile at confidence
level \\(c\\) is:

\\[
q_{{1-c}} = Q_{{1-c}}(R_T)
\\]

The script reports a signed loss amount as:

\\[
\\operatorname{{VaR}}_c = -V_0 q_{{1-c}}
\\]

Expected Shortfall is estimated from the average of returns at or below the
lower-tail quantile:

\\[
\\operatorname{{ES}}_c = -V_0 \\, \\mathbb{{E}}[R_T \\mid R_T \\le q_{{1-c}}]
\\]

Here the implementation uses the empirical mean of simulated returns selected
into the lower tail. In a finite sample, the exact number of observations in the
tail can vary slightly due to ties and quantile conventions.

A positive reported loss amount corresponds to a loss threshold or average loss.
If the modeled lower-tail quantile is positive, the signed VaR loss amount can
be negative; this is mathematically possible and should not be silently changed
to zero.

**VaR limitation:** VaR describes a loss quantile but does not indicate how severe
losses can be beyond that quantile. Expected Shortfall complements it by
summarizing the average loss in the selected tail.

## 5. What each chart tells us

1. **Terminal value distribution** — reveals the spread, central tendency, and
   lower/upper tails of simulated end-of-horizon values.
2. **Sample portfolio paths** — demonstrates the range of possible trajectories
   and how compounding can cause paths to diverge.
3. **Percentile fan chart** — compares daily percentile paths and shows how the
   range of modeled outcomes evolves over time.
4. **VaR versus Expected Shortfall** — compares the loss threshold with the
   average loss beyond that threshold at 95% and 99% confidence.
5. **Terminal return versus portfolio value** — displays individual simulated
   outcomes relative to the starting capital and helps identify modeled gains
   and losses.

The individual path chart is a sample of simulations, not all paths. The terminal
value CSV contains one terminal outcome for every simulation.

## 6. Business and risk-management value

This analysis demonstrates how a quantitative analyst can:

- translate historical asset returns into a probabilistic scenario model;
- preserve estimated cross-asset correlation in simulated returns;
- quantify potential downside using VaR and Expected Shortfall;
- estimate the modeled frequency of ending below a capital threshold;
- communicate uncertainty through percentile charts and distributions;
- produce reproducible, auditable CSV outputs and interactive reports.

A risk manager could use such a framework as an initial scenario-analysis tool,
then compare its estimates with historical stress tests, backtests, and alternative
models before using it for a real risk process.

## 7. Model limitations and validation work still needed

- **Normality:** Multivariate normal returns can underrepresent fat tails and
  extreme joint market moves.
- **Stationarity:** Historical means, volatilities, and correlations may change.
- **Parameter uncertainty:** Estimated means and covariance are not known constants.
- **Regime changes:** The model does not explicitly represent crises or volatility
  clustering.
- **Rebalancing assumption:** Daily equal-weight rebalancing is assumed; real
  portfolios may rebalance less often.
- **Costs:** Transaction costs, taxes, market impact, and slippage are excluded.
- **Concentration:** Five technology-heavy stocks can remain highly exposed to
  common sector and market risks.
- **Model validation:** No out-of-sample calibration or VaR exceedance backtest is
  performed by this script.
- **Benchmark comparison:** The S&P 500 is not included as a portfolio holding in
  this Monte Carlo engine.

Recommended next improvements are historical or block bootstrap simulation,
Student-t innovations, volatility models such as GARCH, stress scenarios, and
out-of-sample backtesting.

## 8. Reproducibility and files

- `simulation_configuration.json` — configuration and model assumptions.
- `simulation_summary.csv` — headline statistics.
- `simulated_var_es.csv` — 95% and 99% tail risk.
- `terminal_values.csv` — all terminal simulated outcomes.
- `sample_simulation_paths.csv` — sample wealth paths.
- `sample_simulated_daily_returns.csv` — sample simulated returns.
- `charts/` — individual interactive Plotly charts.
- `monte_carlo_dashboard.html` — combined interactive dashboard.

The fixed random seed makes the random draw process reproducible for the same
data, code, dependency behavior, and configuration. Minor numerical differences
can occur across environments or numerical library versions.

## 9. Research foundation

See [`docs/REFERENCES.md`](../../docs/REFERENCES.md) for the bibliography and
links to the original papers and book.
"""

    (MC / "monte_carlo_analysis_report.md").write_text(
        report, encoding="utf-8"
    )


def generate_methodology():
    content = r"""# Monte Carlo Portfolio Risk Simulator — Methodology

## Objective

Estimate a distribution of hypothetical terminal portfolio values and downside
risk measures using Monte Carlo simulation calibrated to historical returns.

## Portfolio

Five assets are held at equal weights: AAPL, AMZN, GOOGL, MSFT, and NVDA.
Weights are reset to equal weights every simulated trading day. The S&P 500
benchmark is not included as a holding in this simulation.

## Data and return transformations

Given adjusted or prepared prices \(P_{i,t}\), calculate log returns:

\[
r_{i,t} = \ln(P_{i,t}/P_{i,t-1})
\]

Estimate the sample mean vector \(\hat{\mu}\) and covariance matrix
\(\hat{\Sigma}\) from the observed daily log-return series.

## Monte Carlo model

For every simulation and day, generate correlated asset log returns:

\[
\mathbf{r}_t \sim \mathcal{N}(\hat{\mu},\hat{\Sigma})
\]

Convert them to simple returns:

\[
R_{i,t} = e^{r_{i,t}}-1
\]

Calculate daily equal-weight portfolio returns and compound wealth:

\[
R_{p,t} = \sum_i w_i R_{i,t}, \qquad
V_T = V_0 \prod_{t=1}^{T}(1+R_{p,t})
\]

The covariance matrix is symmetrized and its eigenvalues are floored at a small
positive value for numerical stability before sampling.

## Risk metrics

For terminal simple return \(R_T=V_T/V_0-1\), at confidence level \(c\):

\[
q_{1-c}=Q_{1-c}(R_T)
\]

The signed VaR loss amount is \(-V_0 q_{1-c}\). Expected Shortfall is estimated
as the negative initial-capital-scaled mean of terminal returns at or below
the lower-tail quantile.

Probability of loss is the proportion of simulations with \(V_T<V_0\).
Terminal value percentiles summarize the modeled distribution, not guaranteed
future bounds.

## Important distinctions

- The model simulates a joint distribution of returns; it does not predict a
  specific market path.
- Correlation is estimated from the historical covariance matrix, but may not
  remain stable during stress.
- The Gaussian assumption can understate fat tails and extreme joint events.
- Historical mean and covariance estimates are uncertain.
- No transaction costs, taxes, slippage, or liquidity constraints are included.
- The output is not investment advice or a validated production risk model.

## Suggested validation

1. Compare simulated and historical marginal return distributions.
2. Compare model VaR with realized out-of-sample losses.
3. Perform VaR exception counting and independence/conditional coverage tests.
4. Test block bootstrap and Student-t alternatives.
5. Add volatility models and explicit stress scenarios.
6. Compare results under different estimation windows and rebalancing schedules.
"""
    (DOCS / "MONTE_CARLO_METHODOLOGY.md").write_text(
        content, encoding="utf-8"
    )


def generate_references():
    content = """# Research References

These sources provide the theoretical background for portfolio construction,
risk measurement, and Monte Carlo simulation. The project is an educational
implementation inspired by these concepts; it does not reproduce every method
or validation procedure in the papers.

## 1. Mean-variance portfolio theory

**Markowitz, H. (1952).** Portfolio Selection. *The Journal of Finance, 7*(1), 77–91.

DOI: https://doi.org/10.1111/j.1540-6261.1952.tb01525.x

**Relevance:** Foundational work on portfolio choice and the role of expected
returns, variance, and co-movement. This project uses a covariance matrix to
represent co-movement, but it uses fixed equal weights rather than optimizing
the portfolio.

## 2. Coherent risk measures

**Artzner, P., Delbaen, F., Eber, J.-M., & Heath, D. (1999).**
Coherent Measures of Risk. *Mathematical Finance, 9*(3), 203–228.

DOI: https://doi.org/10.1111/1467-9965.00068

**Relevance:** Develops axiomatic properties for risk measures and discusses
shortcomings of quantile-based measures. Provides background for interpreting
tail-risk estimates carefully.

## 3. Expected Shortfall

**Acerbi, C., & Tasche, D. (2002).** On the Coherence of Expected Shortfall.
*Journal of Banking & Finance, 26*(7), 1487–1503.

DOI: https://doi.org/10.1016/S0378-4266(02)00283-2

**Relevance:** Examines the coherence properties of Expected Shortfall and
distinctions between definitions, particularly for distributions with
discontinuities. This project uses a finite-simulation empirical lower-tail
average as its ES estimate.

## 4. Monte Carlo methods in financial engineering

**Glasserman, P. (2003).** *Monte Carlo Methods in Financial Engineering.*
Springer, Stochastic Modelling and Applied Probability, volume 53.

DOI: https://doi.org/10.1007/978-0-387-21617-1

**Relevance:** Broad reference on Monte Carlo methods in financial engineering,
including simulation design, estimation, and variance reduction. The current
project implements a baseline simulation and does not implement all techniques
covered in the book.

## 5. VaR model backtesting

**Kupiec, P. H. (1995).** Techniques for Verifying the Accuracy of Risk
Measurement Models. *The Journal of Derivatives, 3*(2), 73–84.

DOI: https://doi.org/10.3905/jod.1995.407942

**Relevance:** Background for testing whether realized exceptions are consistent
with the exception frequency implied by a VaR model. A Kupiec test is not
implemented in the current simulation script.

## 6. Conditional coverage and VaR exceptions

**Christoffersen, P. F. (1998).** Evaluating Interval Forecasts.
*International Economic Review, 39*(4), 841–862.

DOI: https://doi.org/10.2307/2527341

**Relevance:** Useful foundation for evaluating interval forecasts and the
independence of forecast violations. It motivates future out-of-sample risk
validation, which is not yet implemented here.

## 7. ARCH effects and volatility clustering

**Engle, R. F. (1982).** Autoregressive Conditional Heteroscedasticity with
Estimates of the Variance of United Kingdom Inflation. *Econometrica, 50*(4),
987–1007.

DOI: https://doi.org/10.2307/1912773

**Relevance:** Foundational ARCH paper. It motivates future extensions that
model time-varying volatility rather than assuming constant historical
covariance throughout the simulated horizon.

## Research-to-code mapping

| Concept | Where used in this project | Status |
|---|---|---|
| Portfolio covariance and co-movement | Historical covariance matrix | Implemented |
| Correlated Monte Carlo draws | `src/monte_carlo_simulation.py` | Implemented |
| Terminal wealth distribution | Terminal value CSV and histogram | Implemented |
| VaR and Expected Shortfall | `simulated_var_es.csv` | Implemented |
| VaR backtesting | Future out-of-sample validation | Not implemented |
| Conditional volatility | Possible GARCH extension | Not implemented |
| Portfolio optimization | Possible mean-variance extension | Not implemented |

## Academic integrity note

Cite the original sources when describing the theoretical background. Clearly
distinguish published research from this repository's implementation, assumptions,
outputs, and limitations. Do not claim the project implements an entire paper
when it only uses a related concept.
"""
    (DOCS / "REFERENCES.md").write_text(content, encoding="utf-8")


def main():
    summary, risk, terminal, terminal_values, terminal_returns, config = read_inputs()

    generate_dashboard(
        summary, risk, terminal_values, terminal_returns, config
    )
    generate_analysis_report(
        summary, risk, terminal, terminal_values, terminal_returns, config
    )
    generate_methodology()
    generate_references()

    print("\nDASHBOARD AND DOCUMENTATION GENERATED")
    print("=" * 55)
    print(f"Dashboard: {MC / 'monte_carlo_dashboard.html'}")
    print(f"Analysis report: {MC / 'monte_carlo_analysis_report.md'}")
    print(f"Methodology: {DOCS / 'MONTE_CARLO_METHODOLOGY.md'}")
    print(f"References: {DOCS / 'REFERENCES.md'}")
    print("\nHeadline results from the saved simulation:")
    print(f"Mean terminal value: ${terminal_values.mean():,.2f}")
    print(f"Median terminal value: ${terminal_values.median():,.2f}")
    print(f"Probability of loss: {(terminal_values < float(summary['Initial_Portfolio_Value'])).mean():.2%}")


if __name__ == "__main__":
    main()
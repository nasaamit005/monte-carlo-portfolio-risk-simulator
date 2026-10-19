# Monte Carlo Portfolio Risk Simulation — Analysis Report

## 1. Executive summary

This project uses Monte Carlo simulation to explore a range of possible one-year
outcomes for a hypothetical equal-weighted portfolio of five US technology
stocks: AAPL, AMZN, GOOGL, MSFT, NVDA. It generates **10,000
simulated paths**, each spanning **252 trading days**,
starting from **$10,000.00**.

The model estimates a mean terminal value of **$13,972.82** and a median
terminal value of **$13,440.80**. The modeled probability of ending below
the initial investment is **14.45%**. The 95% VaR loss estimate is
**$1,452.91**, while the 95% Expected Shortfall estimate is
**$2,323.95**.

These are the outputs of the configured model, not predictions or guaranteed
investment outcomes. The numerical values depend on the sample period, return
distribution assumptions, portfolio weights, and random seed.

## 2. What was analysed

### Historical input data

- Historical start date: 2016-10-17
- Historical end date: 2026-10-16
- Daily return observations: 2,513
- Assets: AAPL, AMZN, GOOGL, MSFT, NVDA
- Starting portfolio value: $10,000.00
- Portfolio weights: equal weights across five stocks
- Rebalancing: daily
- Simulation seed: 42

The price series is converted to daily log returns:

\[
r_{i,t} = \ln\left(\frac{P_{i,t}}{P_{i,t-1}}\right)
\]

For each asset, the sample mean and the joint covariance matrix are estimated
from historical daily log returns. The covariance matrix captures both each
asset's variability and the estimated co-movement between assets.

### Correlated simulation

For each simulated day, the model draws a vector of asset log returns from a
multivariate normal distribution:

\[
\mathbf{r}_t \sim \mathcal{N}(\boldsymbol{\mu}, \boldsymbol{\Sigma})
\]

The simulated log returns are converted to simple returns:

\[
R_{i,t} = e^{r_{i,t}} - 1
\]

With equal weights \(w_i = 1/5\), the portfolio's daily return is:

\[
R_{p,t} = \sum_{i=1}^5 w_i R_{i,t}
\]

The portfolio is rebalanced to equal weights each simulated day. Portfolio
value is compounded through the horizon:

\[
V_T = V_0 \prod_{t=1}^T (1+R_{p,t})
\]

The simulation uses 10,000 paths, each with
252 trading days.

## 3. Main results

| Metric | Result | Interpretation |
|---|---:|---|
| Initial portfolio value | $10,000.00 | Starting hypothetical capital |
| Mean terminal value | $13,972.82 | Average terminal value across simulations |
| Median terminal value | $13,440.80 | Middle simulated outcome |
| Standard deviation of terminal values | $3,930.17 | Spread of terminal dollar values |
| 1st percentile terminal value | $7,060.81 | Very low modeled outcome |
| 5th percentile terminal value | $8,547.09 | Lower-tail outcome |
| 25th percentile terminal value | $11,200.93 | Lower quartile |
| 75th percentile terminal value | $16,215.00 | Upper quartile |
| 95th percentile terminal value | $21,181.09 | Upper-tail outcome |
| 99th percentile terminal value | $25,625.84 | Very high modeled outcome |
| Mean terminal return | 39.73% | Average simulated return |
| Median terminal return | 34.41% | Median simulated return |
| Probability of ending below initial value | 14.45% | Fraction of paths with a loss |
| Probability of ending above initial value | 85.55% | Fraction of paths with a gain |

The percentile values describe the distribution of terminal outcomes. For example,
the 5th percentile means approximately 5% of modeled outcomes are at or below that
value under the model assumptions. It is not a guarantee that future value will
remain above that threshold.

## 4. Value at Risk and Expected Shortfall

| Confidence | VaR loss estimate | Expected Shortfall loss estimate | Tail count |
|---|---:|---:|---:|
| 95% | $1,452.91 | $2,323.95 | 500 |
| 99% | $2,939.19 | $3,466.75 | 100 |

For terminal return \(R_T = V_T/V_0 - 1\), the lower-tail quantile at confidence
level \(c\) is:

\[
q_{1-c} = Q_{1-c}(R_T)
\]

The script reports a signed loss amount as:

\[
\operatorname{VaR}_c = -V_0 q_{1-c}
\]

Expected Shortfall is estimated from the average of returns at or below the
lower-tail quantile:

\[
\operatorname{ES}_c = -V_0 \, \mathbb{E}[R_T \mid R_T \le q_{1-c}]
\]

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

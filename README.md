# Monte Carlo Portfolio Risk Simulator

A Python-based quantitative finance project for simulating portfolio outcomes using Monte Carlo methods, estimating potential investment losses, calculating Value at Risk (VaR) and Expected Shortfall (ES), analyzing portfolio risk, and generating interactive Plotly dashboards.

**GitHub Repository:** `monte-carlo-portfolio-risk-simulator`

## 🌐 Interactive Reports

**Interactive Monte Carlo Dashboard**

Explore portfolio outcome distributions, simulated investment paths, percentile fan charts, terminal-value scenarios, and downside risk metrics using interactive Plotly visualizations.

- [Open Monte Carlo Dashboard](reports/monte_carlo_dashboard.html)
- [Open Monte Carlo Analysis Report](reports/monte_carlo_analysis_report.html)
- [View Interactive Chart Files](reports/monte_carlo/charts/)

These links work when the corresponding HTML files are included in the repository. For a publicly hosted website, publish the HTML reports using GitHub Pages or another static hosting service and replace these links with the resulting public URLs.

## Project Objectives

- Simulate thousands of possible portfolio outcomes over a defined investment horizon.
- Estimate the distribution of future portfolio values.
- Calculate the probability of losing money.
- Measure downside risk using VaR and Expected Shortfall.
- Analyze historical asset returns, volatility, and correlations.
- Visualize portfolio uncertainty using interactive Plotly charts.
- Build a reproducible Python workflow with automated tests.
- Demonstrate quantitative analysis skills relevant to financial analytics and risk analysis.

## Features

- Historical stock-price data collection
- Data validation and preprocessing
- Daily log-return calculations
- Historical mean-return and covariance estimation
- Correlated multivariate Monte Carlo simulation
- Equal-weighted portfolio modeling
- Simulated portfolio growth paths
- Terminal portfolio-value distribution analysis
- Probability-of-loss estimation
- 95% and 99% Value at Risk calculations
- Expected Shortfall analysis
- Interactive Plotly HTML charts
- CSV-based simulation and risk reports
- Reproducible simulations using a fixed random seed
- Automated testing using pytest

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Simulation and financial analysis |
| NumPy | Numerical computation, random sampling, and covariance analysis |
| pandas | Data processing and financial time series |
| yfinance | Historical market-data retrieval |
| Plotly | Interactive charts and dashboards |
| pytest | Automated testing |
| Git and GitHub | Version control and project publication |

## Assets Analyzed

The portfolio includes five large-cap technology stocks:

| Ticker | Company |
|---|---|
| AAPL | Apple |
| AMZN | Amazon |
| GOOGL | Alphabet |
| MSFT | Microsoft |
| NVDA | NVIDIA |

The S&P 500 Index (`^GSPC`) is downloaded as a market benchmark for historical analysis. It is not one of the five equal-weighted portfolio stocks unless the source code is changed.

## Project Structure

```text
monte-carlo-portfolio-risk-simulator/
├── data/
│   ├── raw/
│   │   └── all_tickers_daily.csv
│   └── processed/
│       ├── prices_wide.csv
│       ├── daily_returns.csv
│       ├── performance_metrics.csv
│       ├── stock_correlation.csv
│       └── portfolio_daily_returns.csv
├── docs/
├── reports/
│   ├── monte_carlo_analysis_report.html
│   ├── monte_carlo_dashboard.html
│   └── monte_carlo/
│       ├── charts/
│       │   ├── terminal_value_distribution.html
│       │   ├── sample_simulation_paths.html
│       │   ├── portfolio_percentile_fan.html
│       │   ├── var_es_comparison.html
│       │   └── terminal_outcomes_scatter.html
│       ├── simulation_summary.csv
│       ├── simulated_var_es.csv
│       ├── terminal_values.csv
│       ├── sample_simulation_paths.csv
│       ├── sample_simulated_daily_returns.csv
│       ├── simulation_configuration.json
│       └── monte_carlo_summary.md
├── src/
│   ├── download_data.py
│   ├── validate_data.py
│   ├── portfolio_analysis.py
│   └── monte_carlo_simulation.py
├── tests/
│   └── test_monte_carlo.py
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

*This structure represents the expected project layout. Keep only files that actually exist in your repository, and update the listing if your filenames differ.*


# Key Financial Formulas

These equations describe the main mathematical and financial concepts used in the Monte Carlo Portfolio Risk Simulator. Each equation is followed by the definitions of its symbols.

## 1. Daily Log Return

Daily log return measures the continuously compounded price change between consecutive trading days.

$$
\boxed{
r_{i,t}=\ln\left(\frac{P_{i,t}}{P_{i,t-1}}\right)
}
$$

**Symbols and meanings**

| Symbol | Name | Meaning |
|---|---|---|
| $r_{i,t}$ | Daily log return | Logarithmic return of asset $i$ on day $t$. |
| $P_{i,t}$ | Current price | Adjusted closing price of asset $i$ on day $t$. |
| $P_{i,t-1}$ | Previous price | Adjusted closing price of asset $i$ on the previous trading day. |
| $\ln$ | Natural logarithm | Logarithm to base $e$. |
| $i$ | Asset index | Identifies a stock in the portfolio. |
| $t$ | Time index | Identifies a trading day. |
| $e$ | Euler's number | Mathematical constant approximately equal to $2.71828$. |

## 2. Multivariate Return Simulation

Correlated asset log returns are modeled using a multivariate normal probability distribution.

$$
\boxed{
\mathbf{r}_t\sim\mathcal{N}
\left(\boldsymbol{\mu},\boldsymbol{\Sigma}\right)
}
$$

**Symbols and meanings**

| Symbol | Name | Meaning |
|---|---|---|
| $\mathbf{r}_t$ | Return vector | Vector of simulated log returns for all assets on day $t$. |
| $\mathcal{N}$ | Multivariate normal distribution | Probability distribution used to model the joint asset returns. |
| $\boldsymbol{\mu}$ | Mean vector | Vector of estimated mean log returns for the assets. |
| $\boldsymbol{\Sigma}$ | Covariance matrix | Matrix containing asset-return variances and covariances. |
| $\sim$ | Distributed as | Indicates the probability distribution followed by a random variable. |
| $\mathbf{r}$ | Vector notation | Bold notation indicates a vector of returns rather than one scalar return. |

The covariance matrix represents estimated relationships between asset returns and helps preserve their dependence in simulated scenarios.

## 3. Conversion from Log Return to Simple Return

Simulated log returns are converted to simple returns before calculating weighted portfolio returns.

$$
\boxed{
R_{i,t}=e^{r_{i,t}}-1
}
$$

**Symbols and meanings**

| Symbol | Name | Meaning |
|---|---|---|
| $R_{i,t}$ | Simple return | Percentage price change of asset $i$ on day $t$, expressed as a decimal. |
| $r_{i,t}$ | Log return | Logarithmic return of asset $i$ on day $t$. |
| $e$ | Euler's number | Mathematical constant approximately equal to $2.71828$. |
| $i$ | Asset index | Identifies the asset. |
| $t$ | Time index | Identifies the trading day. |

For example, a simple return of $0.05$ represents a return of $5\%$.

## 4. Equal-Weighted Portfolio Return

The general portfolio return is the weighted sum of the individual asset returns.

$$
\boxed{
R_{p,t}=\sum_{i=1}^{N}w_iR_{i,t}
}
$$

For an equal-weighted portfolio, each asset receives the same weight.

$$
\boxed{
w_i=\frac{1}{N}
}
$$

Substituting the equal weights into the general formula gives:

$$
\boxed{
R_{p,t}=\frac{1}{N}\sum_{i=1}^{N}R_{i,t}
}
$$

**Symbols and meanings**

| Symbol | Name | Meaning |
|---|---|---|
| $R_{p,t}$ | Portfolio return | Portfolio return on day $t$. |
| $R_{i,t}$ | Asset return | Simple return of asset $i$ on day $t$. |
| $w_i$ | Portfolio weight | Proportion of the portfolio allocated to asset $i$. |
| $N$ | Number of assets | Total number of assets included in the portfolio. |
| $\sum$ | Summation operator | Adds the indicated terms together. |
| $i$ | Asset index | Identifies an individual asset. |
| $p$ | Portfolio index | Identifies the portfolio rather than an individual asset. |
| $t$ | Time index | Identifies the trading day. |

Equal weighting means every asset has the same weight. Whether those weights remain constant or are rebalanced during each simulation depends on the implementation.

## 5. Portfolio Value Evolution

Portfolio value evolves by compounding the portfolio returns over successive periods.

$$
\boxed{
V_t=V_0\prod_{k=1}^{t}(1+R_{p,k})
}
$$

**Symbols and meanings**

| Symbol | Name | Meaning |
|---|---|---|
| $V_t$ | Portfolio value | Portfolio value at time $t$. |
| $V_0$ | Initial investment | Portfolio value at the beginning of the simulation. |
| $R_{p,k}$ | Portfolio return | Portfolio return during period $k$. |
| $\prod$ | Product operator | Multiplies the growth factors across all specified periods. |
| $k$ | Period index | Identifies an individual period in the compounding process. |
| $t$ | Time index | Current simulated period. |

Each growth factor, $1+R_{p,k}$, represents the change in portfolio value during one period.

## 6. Terminal Portfolio Return

Terminal return measures the total gain or loss relative to the initial investment at the end of the simulation.

$$
\boxed{
R_p=\frac{V_T}{V_0}-1
}
$$

**Symbols and meanings**

| Symbol | Name | Meaning |
|---|---|---|
| $R_p$ | Terminal portfolio return | Total portfolio return over the simulation horizon. |
| $V_T$ | Terminal portfolio value | Portfolio value at the end of the simulation. |
| $V_0$ | Initial portfolio value | Portfolio value at the beginning of the simulation. |
| $T$ | Final time index | Last period of the simulation. |
| $p$ | Portfolio index | Identifies the portfolio. |

A positive terminal return represents a gain, while a negative terminal return represents a loss.


## 7. Value at Risk (VaR)

Value at Risk estimates a monetary loss threshold at a specified confidence level.

**General formula**

$$
\boxed{\mathrm{VaR}_c=-V_0 Q_{1-c}(R_p)}
$$

**At a 95% confidence level**

$$
\boxed{\mathrm{VaR}_{0.95}=-V_0 Q_{0.05}(R_p)}
$$

### Symbols and meanings

| Symbol | Name | Meaning |
|---|---|---|
| $\mathrm{VaR}_c$ | Value at Risk | Estimated monetary loss threshold at confidence level $c$. |
| $c$ | Confidence level | Risk confidence level, such as $0.95$ for 95%. |
| $V_0$ | Initial investment | Starting monetary value of the portfolio. |
| $R_p$ | Terminal portfolio return | Simulated total portfolio return over the investment horizon. |
| $Q_{1-c}(R_p)$ | Lower-tail quantile | Return threshold at probability $1-c$. |
| $Q$ | Quantile function | Identifies a specified percentile of a return distribution. |

At 95% confidence, the formula uses the 5th percentile of terminal returns. If this quantile is negative, VaR is expressed as a positive monetary loss threshold.

VaR is a model-based estimate, not a guarantee that losses will remain below the stated amount.

---

## 8. Expected Shortfall (ES)

Expected Shortfall estimates the average monetary loss among the worst outcomes in the selected lower tail of the return distribution.

**General formula**

$$
\boxed{\mathrm{ES}_c=-V_0\,\mathbb{E}\left[R_p\mid R_p\leq Q_{1-c}(R_p)\right]}
$$

**At a 95% confidence level**

$$
\boxed{\mathrm{ES}_{0.95}=-V_0\,\mathbb{E}\left[R_p\mid R_p\leq Q_{0.05}(R_p)\right]}
$$

### Symbols and meanings

| Symbol | Name | Meaning |
|---|---|---|
| $\mathrm{ES}_c$ | Expected Shortfall | Average monetary loss in the selected worst-return tail. |
| $c$ | Confidence level | Risk confidence level, such as $0.95$ for 95%. |
| $V_0$ | Initial investment | Initial monetary value of the portfolio. |
| $R_p$ | Terminal portfolio return | Simulated total portfolio return. |
| $\mathbb{E}$ | Expected value operator | Calculates the average of values under the specified condition. |
| $\mid$ | Conditional operator | Means the calculation applies only when the stated condition holds. |
| $Q_{1-c}(R_p)$ | Lower-tail quantile | Return threshold defining the worst $1-c$ fraction of outcomes. |
| $\leq$ | Less-than-or-equal-to operator | Selects returns at or below the threshold. |

At 95% confidence, Expected Shortfall considers the worst 5% of terminal-return outcomes. Under this convention, a negative average return in that tail produces a positive monetary loss estimate.

---


## 9. Probability of Loss

The probability of loss estimates the fraction of simulated scenarios in which the terminal portfolio value is below the initial investment.

**General formula**

$$
P(\text{Loss}) = \frac{1}{M}\sum_{j=1}^{M} I(V_T^{(j)} < V_0)
$$

**Expressed as a percentage**

$$
\text{Probability of Loss (\%)} = 100 \times P(\text{Loss})
$$

### Symbols and meanings

| Symbol | Name | Meaning |
|---|---|---|
| $P(\text{Loss})$ | Probability of loss | Fraction of simulations that end below the initial investment. |
| $M$ | Number of simulations | Total number of Monte Carlo simulation paths. |
| $j$ | Simulation index | Identifies an individual simulation path. |
| $V_T^{(j)}$ | Simulated terminal portfolio value | Portfolio value at the end of simulation $j$. |
| $V_0$ | Initial investment | Starting monetary value of the portfolio. |
| $I(\cdot)$ | Indicator function | Equals 1 if the condition is true and 0 otherwise. |
| $<$ | Less-than operator | Tests whether the terminal value is below the initial investment. |
| $\times 100$ | Percentage conversion | Converts the probability from a decimal into a percentage. |

**Example**

If 1,500 out of 10,000 simulations finish below the initial investment:

$$
P(\text{Loss}) = \frac{1500}{10000} = 0.15
$$

$$
\text{Probability of Loss} = 0.15 \times 100 = 15\%
$$

This probability is an estimate based on the model assumptions and historical inputs. It is not a guarantee of future investment performance.


$$
\text{Probability of Loss}=\frac{1500}{10000}\times100=15\%
$$

This probability is an estimate based on the model assumptions and historical inputs. It is not a guarantee of future investment performance.

---

**Implementation note:** These equations describe the intended mathematical framework. Verify the current Python implementation before claiming that each equation exactly matches the code, particularly the portfolio rebalancing method and the calculations used for VaR and Expected Shortfall.



## Simulation Configuration

The current configuration used in an earlier simulation run was:

| Parameter | Value |
|---|---:|
| Number of simulations | 10,000 |
| Investment horizon | 252 trading days |
| Initial portfolio value | $10,000 |
| Portfolio allocation | Equal-weighted |
| Random seed | 42 |
| Annual trading-day convention | 252 days |

These are configurable settings, not guarantees. Check the current source code and `simulation_configuration.json` to confirm the settings used in your latest run.

## Example Monte Carlo Results

An earlier simulation produced the following results:

| Metric | Result |
|---|---:|
| Mean terminal portfolio value | $13,972.82 |
| Median terminal portfolio value | $13,440.80 |
| 5th percentile terminal value | $8,547.09 |
| 95th percentile terminal value | $21,181.09 |
| Probability of loss | 14.45% |
| 95% VaR | $1,452.91 |
| 95% Expected Shortfall | $2,323.95 |
| 99% VaR | $2,939.19 |
| 99% Expected Shortfall | $3,466.75 |

**Important:** These figures are from an earlier run. Rerun the simulator and verify the latest generated reports before presenting them as current results.

## Interactive Dashboards

The project generates interactive Plotly HTML visualizations for:

| Chart or Report | Purpose |
|---|---|
| Terminal value distribution | Explore the distribution of simulated ending portfolio values |
| Sample simulation paths | Compare example portfolio trajectories |
| Portfolio percentile fan | Visualize the range of simulated outcomes over time |
| VaR and ES comparison | Compare downside risk measures at different confidence levels |
| Terminal outcomes scatter | Explore individual simulated terminal outcomes |
| Monte Carlo dashboard | Review selected simulation results in one place |
| Monte Carlo analysis report | Review the broader analysis and methodology |

The individual charts are saved in `reports/monte_carlo/charts/`.

To open a chart, navigate to the relevant HTML file in VS Code Explorer and select **Reveal in File Explorer**, then open it in a web browser. The charts can also be opened directly from your local project directory.

For a public live website, deploy the HTML reports to GitHub Pages or another static hosting service. Local file links are not public web links.

## Installation

### 1. Clone the repository

Replace `YOUR-USERNAME` with your GitHub username after publishing the repository.

```bash
git clone https://github.com/YOUR-USERNAME/monte-carlo-portfolio-risk-simulator.git
cd monte-carlo-portfolio-risk-simulator
```

### 2. Create a virtual environment

For Windows with Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use an appropriate process-scoped execution policy or run the commands in a terminal where activation is permitted.

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run the Project

Run the scripts from the repository root in the appropriate order.

### Download historical market data

```powershell
python .\src\download_data.py
```

### Validate downloaded data

```powershell
python .\src\validate_data.py
```

### Generate portfolio performance analysis

```powershell
python .\src\portfolio_analysis.py
```

### Run Monte Carlo simulation

```powershell
python .\src\monte_carlo_simulation.py
```

### Run automated tests

```powershell
python -m pytest -v
```

These commands assume the corresponding files exist in `src/`. Use the filenames present in your repository if your local scripts differ.

## Testing

The project includes automated tests in `tests/test_monte_carlo.py`.

The test suite is intended to check core simulation behavior, including input validation, reproducibility, covariance handling, terminal-value validation, and risk-metric calculations.

Run the tests after changing the simulation code:

```powershell
python -m pytest -v
```

Report the actual test results from your latest run rather than relying on a previous test count.

## Risk Interpretation

VaR and Expected Shortfall summarize different aspects of downside risk:

- **VaR** estimates a loss threshold at a selected confidence level.
- **Expected Shortfall** estimates the average loss among outcomes in the selected worst tail.
- **Probability of loss** estimates the proportion of simulations ending below the initial portfolio value.
- **Terminal value percentiles** illustrate the spread of possible ending portfolio values under the model.

These measures describe model-generated scenarios. They do not predict the exact future value of a portfolio.

## Limitations

- Historical return distributions may not represent future market conditions.
- The multivariate normal assumption may underrepresent extreme market events and fat tails.
- Historical mean returns and covariance estimates are subject to sampling error.
- Market volatility and correlations can change over time.
- The model may not fully capture volatility clustering, market regimes, or liquidity shocks.
- Transaction costs, taxes, slippage, and market impact may not be included.
- Portfolio rebalancing assumptions may differ from actual investor behavior.
- Monte Carlo output depends on model assumptions, input data, and configuration.
- Historical and simulated outcomes do not guarantee future performance.

## Future Improvements

- Add Student's t-distribution or other fat-tailed return models.
- Incorporate volatility models such as GARCH.
- Add historical simulation and bootstrap-based scenario analysis.
- Include transaction costs, taxes, and rebalancing constraints.
- Compare equal-weighted and alternative portfolio allocations.
- Add stress testing and extreme-event scenarios.
- Introduce walk-forward parameter estimation.
- Add continuous integration with GitHub Actions.
- Publish a hosted dashboard and updated results report.

## Author

**Amit Singh**

GitHub: [@nasaamit005](https://github.com/nasaamit005)

## License

If the repository includes a `LICENSE` file, see that file for the applicable terms. If you intend to distribute this project under the MIT License, include a valid MIT license file in the repository.

---

*Portfolio project demonstrating Python-based quantitative finance, Monte Carlo simulation, portfolio risk measurement, statistical modeling, interactive visualization, and automated testing. For educational and analytical purposes only; not investment advice.*

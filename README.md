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

Key Financial Formulas
1. Daily Log Return
\[
r_{i,t}=\ln\left(\frac{P_{i,t}}{P_{i,t-1}}\right)
\]

2. Multivariate Return Simulation
\[
\mathbf{r}_t\sim\mathcal{N}(\boldsymbol{\mu},\boldsymbol{\Sigma})
\]

3. Conversion from Log Return to Simple Return
\[
R_{i,t}=e^{r_{i,t}}-1
\]

4. Equal-Weighted Portfolio Return
General portfolio return:
\[
R_{p,t}=\sum_{i=1}^{N}w_iR_{i,t}
\]

Equal weight for each asset:
\[
w_i=\frac{1}{N}
\]

Equal-weighted portfolio return:
\[
R_{p,t}=\frac{1}{N}\sum_{i=1}^{N}R_{i,t}
\]

5. Portfolio Value Evolution
\[
V_t=V_0\prod_{k=1}^{t}(1+R_{p,k})
\]

6. Terminal Portfolio Return
\[
R_p=\frac{V_T}{V_0}-1
\]

7. Value at Risk (VaR)
\[
\operatorname{VaR}_c=-V_0Q_{1-c}(R_p)
\]

At a 95% confidence level:
\[
\operatorname{VaR}_{0.95}=-V_0Q_{0.05}(R_p)
\]

8. Expected Shortfall (ES)
\[
\operatorname{ES}_c=-V_0\mathbb{E}\left[R_p\mid R_p\leq Q_{1-c}(R_p)\right]
\]

At a 95% confidence level:
\[
\operatorname{ES}_{0.95}=-V_0\mathbb{E}\left[R_p\mid R_p\leq Q_{0.05}(R_p)\right]
\]

9. Probability of Loss
\[
\Pr(V_T<V_0)=\frac{1}{M}\sum_{j=1}^{M}\mathbf{1}\left(V_T^{(j)}<V_0\right)
\]

Expressed as a percentage:
\[
\text{Probability of Loss (\%)}=\Pr(V_T<V_0)\times100
\]

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

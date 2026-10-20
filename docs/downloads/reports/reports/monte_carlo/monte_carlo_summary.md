# Monte Carlo Portfolio Risk Simulation

## Model setup

- Simulations: 10,000
- Horizon: 252 trading days
- Initial portfolio value: $10,000.00
- Assets: AAPL, AMZN, GOOGL, MSFT, NVDA
- Portfolio weights: equal-weighted, rebalanced daily
- Historical return observations: 2,513
- Estimation period: 2016-10-17 to 2026-10-16
- Random seed: 42

## Simulated results

- Mean terminal value: $13,972.82
- Median terminal value: $13,440.80
- 5th percentile terminal value: $8,547.09
- 95th percentile terminal value: $21,181.09
- Probability of ending below the initial value: 14.45%
- Worst simulated terminal value: $4,975.87
- Best simulated terminal value: $37,082.93

## Tail-risk estimates

- 95% VaR loss estimate: $1,452.91
- 95% Expected Shortfall estimate: $2,323.95
- 99% VaR loss estimate: $2,939.19
- 99% Expected Shortfall estimate: $3,466.75

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

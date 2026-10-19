# Monte Carlo vs GARCH Portfolio Risk Comparison

## Experimental setup

- Assets: AAPL, AMZN, GOOGL, MSFT, NVDA
- Simulations per model: 10,000
- Horizon: 252 trading days
- Initial portfolio value: $10,000.00
- Daily portfolio rebalancing: equal weights
- Training/holdout split: chronological 80%/20%

## Results

### Multivariate Normal

- Mean terminal value: $14,210.08
- Median terminal value: $13,628.99
- Probability of loss: 13.97%
- 95% VaR: $1,455.50
- 95% Expected Shortfall: $2,345.24
- 99% VaR: $2,984.64
- 99% Expected Shortfall: $3,517.86

### GARCH(1,1) + Joint Residual Bootstrap

- Mean terminal value: $14,571.12
- Median terminal value: $13,871.93
- Probability of loss: 11.05%
- 95% VaR: $1,145.81
- 95% Expected Shortfall: $2,226.71
- 99% VaR: $2,924.60
- 99% Expected Shortfall: $3,746.47

## Methodology

The baseline simulates correlated multivariate-normal daily log returns using the training sample's mean and covariance.

The GARCH model fits a GARCH(1,1) volatility process to each asset. Aligned historical standardized residual vectors are resampled jointly to preserve empirical cross-asset dependence.

Both models use the same training period, simulation count, horizon, initial investment, equal portfolio weights, daily rebalancing, and quantile-based VaR/ES definitions.

## Limitations

- This is a model comparison, not proof of predictive superiority.
- GARCH marginal volatility models do not constitute a full multivariate GARCH model.
- Joint residual bootstrap preserves observed cross-asset shock vectors but does not model dynamic correlations explicitly.
- Results depend on the estimation period and assumptions.
- Transaction costs, taxes, liquidity, and slippage are excluded.
- A chronological holdout is reserved but is not used in fitting or in the simulation comparison.
- VaR and Expected Shortfall are model-based estimates, not guarantees.

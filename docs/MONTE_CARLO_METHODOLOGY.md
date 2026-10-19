# Monte Carlo Portfolio Risk Simulator — Methodology

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

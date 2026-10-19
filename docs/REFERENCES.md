# Research References

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

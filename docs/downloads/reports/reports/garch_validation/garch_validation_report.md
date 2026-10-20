# GARCH Out-of-Sample Volatility Validation

## Evaluation design

- Training observations: 2,010
- Training period: 2016-10-18 to 2024-10-14
- Holdout observations: 503
- Holdout period: 2024-10-15 to 2026-10-16
- Assets evaluated: AAPL, AMZN, GOOGL, MSFT, NVDA
- GARCH parameters are estimated using training data only.
- Holdout returns are used only after each daily forecast.
- The benchmark uses expanding historical sample variance.
- Both models are evaluated against squared returns demeaned by the training-sample mean.

## QLIKE results

| Asset   | Model                         |   Holdout_Observations |   QLIKE_Mean |
|:--------|:------------------------------|-----------------------:|-------------:|
| AAPL    | GARCH(1,1)                    |                    503 |      1.99167 |
| AAPL    | Expanding Historical Variance |                    503 |      2.17351 |
| AMZN    | GARCH(1,1)                    |                    503 |      2.49629 |
| AMZN    | Expanding Historical Variance |                    503 |      2.50631 |
| GOOGL   | GARCH(1,1)                    |                    503 |      2.41152 |
| GOOGL   | Expanding Historical Variance |                    503 |      2.39871 |
| MSFT    | GARCH(1,1)                    |                    503 |      2.19282 |
| MSFT    | Expanding Historical Variance |                    503 |      2.19456 |
| NVDA    | GARCH(1,1)                    |                    503 |      2.95032 |
| NVDA    | Expanding Historical Variance |                    503 |      3.07226 |

Lower QLIKE indicates a better score for the same target and evaluation sample.

## Interpretation

A positive QLIKE improvement means GARCH had a lower mean QLIKE loss than the historical baseline. A negative value means the historical baseline performed better.

Squared returns are noisy proxies for latent variance. The comparison evaluates forecasts, not future investment returns or profitability.

## Limitations

- The model uses a constant conditional mean.
- GARCH assumes a GARCH(1,1) conditional variance process.
- The historical baseline is an expanding-variance benchmark.
- Results depend on the chosen training and holdout periods.
- Forecast comparisons do not guarantee future performance.

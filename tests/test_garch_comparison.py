
import numpy as np

from src.garch_portfolio_simulation import (
    calculate_metrics,
    portfolio_wealth_paths,
)


def test_risk_metrics_return_expected_columns():
    terminal_values = np.array([8000, 9000, 10000, 11000, 12000])

    result = calculate_metrics(terminal_values, "Test Model")

    assert result["Model"] == "Test Model"
    assert result["Probability_Of_Loss_Percent"] == 40.0
    assert "VaR_95_Amount" in result
    assert "ES_95_Amount" in result
    assert "VaR_99_Amount" in result
    assert "ES_99_Amount" in result


def test_portfolio_wealth_paths_have_expected_shape():
    rng = np.random.default_rng(123)

    simulated_log_returns = rng.normal(
        loc=0.0002,
        scale=0.01,
        size=(8, 20, 5),
    )

    wealth = portfolio_wealth_paths(simulated_log_returns)

    assert wealth.shape == (8, 20)
    assert np.isfinite(wealth).all()
    assert (wealth >= 0).all()


def test_constant_terminal_values_have_zero_loss_probability():
    terminal_values = np.full(100, 12000.0)

    result = calculate_metrics(terminal_values, "Constant Model")

    assert result["Probability_Of_Loss_Percent"] == 0.0
    assert result["VaR_95_Amount"] < 0.0
